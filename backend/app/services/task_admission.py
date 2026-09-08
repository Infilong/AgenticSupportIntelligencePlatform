"""Atomic task admission with snapshotted settings and caller-bound idempotency."""

import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.audit import AuditLog
from app.models.task import SupportTask, TaskExecution
from app.models.task_attempt import TaskAttempt
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.record_input import RecordInput
from app.services.agent_run_context import prepare_agent_run
from app.services.budget_policy_service import BudgetPolicyService
from app.services.task_attempt_context import retry_context
from app.services.workspace_service import permissions_for_role


class TaskAdmissionError(ValueError):
    pass


def admit_task(db: Session, *, workspace_id: UUID, agent_id: UUID, user_id: UUID,
               message: str, request_key: str, language: str | None = None,
               parent_run_id: UUID | None = None, corrected_instructions: str = "",
               record_input: RecordInput | None = None, clarification_reply: str | None = None
               ) -> tuple[SupportTask, GraphRun]:
    message, request_key = message.strip(), request_key.strip()
    if record_input is not None and (
            parent_run_id or record_input.processing_text().strip() != message):
        raise TaskAdmissionError("Original input must match a new record, not a retry.")
    corrected_instructions = corrected_instructions.strip()
    if clarification_reply is not None:
        clarification_reply = clarification_reply.strip()
        if (not parent_run_id or corrected_instructions or not clarification_reply
                or len(clarification_reply) > 2000 or clarification_reply != message):
            raise TaskAdmissionError("Clarification requires a parent and matching nonblank reply.")
    if len(corrected_instructions) > 2000 or (corrected_instructions and not parent_run_id):
        raise TaskAdmissionError("Corrections require a parent run and at most 2000 characters.")
    if not message or len(message) > 12000 or not request_key or len(request_key) > 100:
        raise TaskAdmissionError("Request message or idempotency key is invalid.")
    fingerprint = [str(user_id), str(agent_id), message, language]
    if record_input is not None:
        fingerprint.append(record_input.canonical_json())
    if parent_run_id:
        fingerprint.extend([str(parent_run_id), corrected_instructions])
    if clarification_reply is not None:
        fingerprint.extend(["clarification", clarification_reply])
    request_hash = hashlib.sha256(json.dumps(fingerprint,
                                             ensure_ascii=False).encode()).hexdigest()
    # Permission check precedes even default policy creation. Recheck under the
    # admission lock because default creation can commit and release locks.
    preliminary = db.scalar(select(WorkspaceMember).join(Workspace).where(
        WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id,
        Workspace.deleted_at.is_(None), Workspace.archived_at.is_(None))
        .with_for_update(of=Workspace, key_share=True).execution_options(populate_existing=True))
    if preliminary is None or "agents:run" not in permissions_for_role(preliminary.role):
        raise TaskAdmissionError("Active workspace run permission is required.")
    budget = BudgetPolicyService(db)
    budget.get_or_create(workspace_id=workspace_id)
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id)
                          .with_for_update(key_share=True).execution_options(populate_existing=True))
    membership = db.scalar(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id,
    ).execution_options(populate_existing=True))
    if (workspace is None or workspace.deleted_at or workspace.archived_at or membership is None
            or "agents:run" not in permissions_for_role(membership.role)):
        raise TaskAdmissionError("Active workspace run permission is required.")
    attempt = db.scalar(select(TaskAttempt).where(TaskAttempt.workspace_id == workspace_id,
        TaskAttempt.request_key == request_key)) if parent_run_id else None
    if attempt:
        if attempt.request_hash != request_hash:
            raise TaskAdmissionError("Idempotency key was already used for a different request.")
        task_id = db.get(TaskExecution, attempt.graph_run_id).task_id
        return db.get(SupportTask, task_id), db.get(GraphRun, attempt.graph_run_id)
    existing = db.scalar(select(SupportTask).where(
        SupportTask.workspace_id == workspace_id, SupportTask.request_key == request_key))
    if existing and not parent_run_id:
        if existing.request_hash != request_hash:
            raise TaskAdmissionError("Idempotency key was already used for a different request.")
        execution = db.scalar(select(TaskExecution).join(GraphRun,
            GraphRun.id == TaskExecution.graph_run_id).where(TaskExecution.task_id == existing.id)
            .order_by(GraphRun.created_at, GraphRun.id).limit(1))
        return existing, db.get(GraphRun, execution.graph_run_id)
    agent = db.scalar(select(AgentConfig).where(
        AgentConfig.id == agent_id, AgentConfig.workspace_id == workspace_id,
    ).execution_options(populate_existing=True))
    if agent is None or not agent.active or agent.archived_at:
        raise TaskAdmissionError("An available workspace agent is required.")
    if budget.rate_limit_exceeded(workspace_id=workspace_id):
        raise TaskAdmissionError("Workspace run rate limit exceeded.")
    token_budget = budget.effective_run_token_budget(workspace_id=workspace_id,
                                                    agent_token_budget=agent.token_budget)
    settings = json.loads(agent.settings_json)
    if not isinstance(settings, dict):
        raise TaskAdmissionError("Agent settings must be an object.")
    history = None
    if parent_run_id:
        try:
            task, history = retry_context(db, workspace_id=workspace_id,
                parent_run_id=parent_run_id, agent_id=agent_id,
                clarification=clarification_reply is not None)
        except ValueError as error:
            raise TaskAdmissionError(str(error)) from error
    else:
        task = SupportTask(workspace_id=workspace_id, created_by_user_id=user_id,
            agent_config_id=agent_id, request_key=request_key, request_hash=request_hash,
            input_message=message,
            input_envelope_json=record_input.canonical_json() if record_input else None)
        db.add(task)
    run, state = prepare_agent_run(db, workspace_id=workspace_id, agent=agent,
        current_user=db.get(User, user_id), input_message=message, token_budget=token_budget,
        settings=settings, language=language, commit=False)
    run.status = GraphRunStatus.queued
    if parent_run_id:
        state["attempt_instructions"] = corrected_instructions
        state["task_history"] = history
    db.add(TaskExecution(workspace_id=workspace_id, task_id=task.id, graph_run_id=run.id,
        initial_state_json=json.dumps(state, ensure_ascii=False), agent_snapshot_json=json.dumps({
            "name": agent.name, "model_config_id": state["agent_model_config_id"],
            "token_budget": token_budget, "settings": settings,
        }, ensure_ascii=False)))
    if parent_run_id:
        db.add(TaskAttempt(workspace_id=workspace_id, graph_run_id=run.id,
            parent_run_id=parent_run_id, request_key=request_key, request_hash=request_hash,
            corrected_instructions=corrected_instructions, clarification_reply=clarification_reply))
    if clarification_reply is not None:
        parent = db.scalar(select(GraphRun).where(GraphRun.id == parent_run_id,
                                                  GraphRun.workspace_id == workspace_id))
        parent.status = GraphRunStatus.completed
        parent.route_decision = "clarification_received"
        db.add(AuditLog(workspace_id=workspace_id, actor_user_id=user_id,
            action="record.clarification_received", resource_type="support_task",
            resource_id=str(task.id), metadata_json=json.dumps({
                "parent_run_id": str(parent_run_id), "run_id": str(run.id)})))
    db.commit()
    return task, run
