"""Exact-proposal authorization and atomic internal side effects; no external calls."""

import json
import time
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.audit import AuditLog
from app.models.task import SupportTask, TaskExecution
from app.models.task_action import TaskActionProposal, TaskNote
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.task_action import TaskActionInput, proposal_hash
from app.services.action_trace import record_action
from app.services.workspace_service import permissions_for_role


class TaskActionError(ValueError):
    pass


def _permissions(db, workspace_id, user_id):
    member = db.scalar(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id,
    ).execution_options(populate_existing=True))
    return permissions_for_role(member.role) if member else []


def _capability(db, run, execution, action):
    agent = db.scalar(select(AgentConfig).where(AgentConfig.id == run.agent_config_id,
        AgentConfig.workspace_id == run.workspace_id).execution_options(populate_existing=True))
    snapshot = json.loads(execution.agent_snapshot_json)["settings"]
    if (agent is None or not agent.active or agent.archived_at
            or action not in json.loads(agent.settings_json).get("allowed_actions", [])
            or action not in snapshot.get("allowed_actions", [])
            or "agents:run" not in _permissions(db, run.workspace_id, run.user_id)):
        raise TaskActionError("Agent or initiating user no longer permits this action.")


def stage_proposal(db: Session, *, run: GraphRun, inputs: TaskActionInput) -> TaskActionProposal:
    """Called inside worker publication under its run lock; caller commits the transaction."""
    execution = db.get(TaskExecution, run.id)
    if execution is None or execution.workspace_id != run.workspace_id:
        raise TaskActionError("A durable task execution is required.")
    if run.status != GraphRunStatus.running or execution.stop_requested_at:
        raise TaskActionError("Only active work can propose an action.")
    _capability(db, run, execution, inputs.action)
    task = db.scalar(select(SupportTask).where(SupportTask.id == execution.task_id,
        SupportTask.workspace_id == run.workspace_id))
    if task is None:
        raise TaskActionError("Task was not found.")
    encoded = inputs.canonical()
    digest = proposal_hash(workspace_id=run.workspace_id, run_id=run.id,
                           task_id=task.id, inputs=encoded)
    existing = db.scalar(select(TaskActionProposal).where(
        TaskActionProposal.graph_run_id == run.id, TaskActionProposal.proposal_hash == digest))
    if existing:
        return existing
    proposal = TaskActionProposal(workspace_id=run.workspace_id, graph_run_id=run.id,
        task_id=task.id, inputs_json=encoded, proposal_hash=digest)
    db.add(proposal)
    db.flush()
    db.add(AuditLog(workspace_id=run.workspace_id, actor_user_id=run.user_id,
        action="task_action.proposed", resource_type="task_action", resource_id=str(proposal.id),
        metadata_json=json.dumps({"proposal_hash": digest, "action": inputs.action})))
    return proposal


def resolve_proposal(db: Session, *, workspace_id: UUID, proposal_id: UUID,
                     reviewer_id: UUID, expected_hash: str, approve: bool,
                     reason: str = "") -> TaskActionProposal:
    started = time.perf_counter()
    # Membership mutations and stop take workspace first. Run locking then serializes
    # action execution with confirmed stopping; all local writes share one transaction.
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id)
                          .with_for_update(key_share=True).execution_options(populate_existing=True))
    if (workspace is None or workspace.archived_at or workspace.deleted_at
            or "reviews:resolve" not in _permissions(db, workspace_id, reviewer_id)):
        raise TaskActionError("Active workspace review permission is required.")
    proposal = db.scalar(select(TaskActionProposal).where(
        TaskActionProposal.id == proposal_id, TaskActionProposal.workspace_id == workspace_id,
    ).execution_options(populate_existing=True))
    if proposal is None:
        raise TaskActionError("Proposal was not found.")
    run = db.scalar(select(GraphRun).where(GraphRun.id == proposal.graph_run_id,
        GraphRun.workspace_id == workspace_id).with_for_update()
        .execution_options(populate_existing=True))
    proposal = db.scalar(select(TaskActionProposal).where(TaskActionProposal.id == proposal_id,
        TaskActionProposal.workspace_id == workspace_id).with_for_update()
        .execution_options(populate_existing=True))
    actual_hash = proposal_hash(workspace_id=workspace_id, run_id=proposal.graph_run_id,
                               task_id=proposal.task_id, inputs=proposal.inputs_json)
    if expected_hash != proposal.proposal_hash or expected_hash != actual_hash:
        raise TaskActionError("Proposal changed. Review the exact inputs again.")
    target = "applied" if approve else "rejected"
    if proposal.status == target:
        return proposal
    if proposal.status != "pending":
        raise TaskActionError("Proposal was already resolved differently.")
    if not approve and (not reason.strip() or len(reason) > 2000):
        raise TaskActionError("A rejection reason of at most 2000 characters is required.")
    execution = db.get(TaskExecution, proposal.graph_run_id, populate_existing=True)
    if (run is None or run.status != GraphRunStatus.needs_human_review
            or execution is None or execution.workspace_id != workspace_id
            or execution.task_id != proposal.task_id or execution.stop_requested_at):
        raise TaskActionError("Run is no longer awaiting action approval.")
    inputs = TaskActionInput.model_validate_json(proposal.inputs_json)
    result = {"action": inputs.action, "applied": approve}
    if approve:
        _capability(db, run, execution, inputs.action)
        task = db.scalar(select(SupportTask).where(SupportTask.id == proposal.task_id,
            SupportTask.workspace_id == workspace_id).with_for_update()
            .execution_options(populate_existing=True))
        if task is None:
            raise TaskActionError("Task was not found.")
        if inputs.action == "set_category":
            inputs.canonical()
            task.category = inputs.value
        else:
            note = db.scalar(select(TaskNote).where(TaskNote.workspace_id == workspace_id,
                TaskNote.task_id == task.id, TaskNote.content == inputs.value).limit(1))
            result["reused"] = note is not None
            if note is None:
                note = TaskNote(workspace_id=workspace_id, task_id=task.id,
                                proposal_id=proposal.id, content=inputs.value)
                db.add(note)
                db.flush()
            result["note_id"] = str(note.id)
    proposal.status = target
    proposal.reviewer_id = reviewer_id
    proposal.reason = reason.strip() if not approve else None
    proposal.resolved_at = datetime.now(UTC)
    proposal.result_json = json.dumps(result, sort_keys=True)
    if approve:
        record_action(db, proposal, max(1, int((time.perf_counter() - started) * 1000)))
    db.add(AuditLog(workspace_id=workspace_id, actor_user_id=reviewer_id,
        action=f"task_action.{target}", resource_type="task_action", resource_id=str(proposal.id),
        metadata_json=json.dumps({"proposal_hash": actual_hash, **result}, sort_keys=True)))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return proposal
