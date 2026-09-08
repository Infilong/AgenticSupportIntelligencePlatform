"""Durable stop requests; active execution must acknowledge before becoming stopped."""

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Checkpoint, GraphRun, GraphRunStatus
from app.models.audit import AuditLog
from app.models.review import HumanReview, ReviewDecision
from app.models.task import TaskExecution
from app.models.task_action import TaskActionProposal
from app.models.workspace import Workspace, WorkspaceMember
from app.services.action_review_gate import reject_actions
from app.services.workspace_service import permissions_for_role


class TaskControlError(ValueError):
    pass


def request_stop(db: Session, *, workspace_id: UUID, run_id: UUID, user_id: UUID) -> GraphRun:
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id)
                          .with_for_update(key_share=True).execution_options(populate_existing=True))
    # FOR NO KEY UPDATE still serializes workspace mutations, but permits child
    # checkpoint/audit FK checks while their owner holds the run lock we need next.
    member = db.scalar(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id,
    ).execution_options(populate_existing=True))
    if (workspace is None or workspace.deleted_at or workspace.archived_at or member is None
            or "agents:run" not in permissions_for_role(member.role)):
        raise TaskControlError("Active workspace run permission is required.")
    execution = db.scalar(select(TaskExecution).where(
        TaskExecution.workspace_id == workspace_id, TaskExecution.graph_run_id == run_id))
    if execution is None:
        raise TaskControlError("Task execution was not found.")
    # Review transitions acquire review then run. Use that same order to avoid a
    # stop/resolve deadlock and prevent publication after a confirmed review stop.
    reviews = list(db.scalars(select(HumanReview).where(
        HumanReview.workspace_id == workspace_id, HumanReview.graph_run_id == run_id,
    ).order_by(HumanReview.id).with_for_update().execution_options(populate_existing=True)))
    run = db.scalar(select(GraphRun).where(GraphRun.id == run_id,
        GraphRun.workspace_id == workspace_id).with_for_update()
        .execution_options(populate_existing=True))
    if run is None:
        raise TaskControlError("Task run was not found.")
    if run.status in {GraphRunStatus.stopping, GraphRunStatus.stopped}:
        return run
    if run.status not in {GraphRunStatus.queued, GraphRunStatus.running,
                          GraphRunStatus.needs_human_review, GraphRunStatus.awaiting_clarification}:
        raise TaskControlError("Finished work cannot be stopped.")
    now = datetime.now(UTC)
    proposals = list(db.scalars(select(TaskActionProposal).where(
        TaskActionProposal.workspace_id == workspace_id,
        TaskActionProposal.graph_run_id == run_id, TaskActionProposal.status == "pending")))
    reject_actions(db, proposals, user_id, "Run stopped before action approval.")
    execution.stop_requested_at = now
    execution.stopped_by_user_id = user_id
    active = run.status == GraphRunStatus.running
    run.status = GraphRunStatus.stopping if active else GraphRunStatus.stopped
    run.final_answer = None
    run.route_decision = "stop_requested" if active else "stopped"
    run.completed_at = None if active else now
    for review in reviews:
        if review.reviewer_decision == ReviewDecision.pending:
            review.reviewer_decision = ReviewDecision.rejected
            review.reviewer_id = user_id
            review.comments = "Run stopped by an administrator."
            review.resolved_at = now
    details = json.dumps({"status": run.status, "user_id": str(user_id)}, sort_keys=True)
    db.add(Checkpoint(workspace_id=workspace_id, graph_run_id=run_id,
                      checkpoint_key="stop_requested", state_json=details))
    db.add(AuditLog(workspace_id=workspace_id, actor_user_id=user_id,
        action="task_run.stop_requested", resource_type="graph_run", resource_id=str(run_id),
        metadata_json=details))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return run
