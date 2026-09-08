"""Validate linked attempts and capture bounded, non-evidence task history."""

from sqlalchemy import func, select

from app.models.agent import GraphRun
from app.models.task import SupportTask, TaskExecution
from app.models.task_action import TaskNote


def retry_context(db, *, workspace_id, parent_run_id, agent_id, clarification=False):
    parent = db.scalar(select(GraphRun).where(GraphRun.id == parent_run_id,
        GraphRun.workspace_id == workspace_id))
    execution = db.scalar(select(TaskExecution).where(TaskExecution.graph_run_id == parent_run_id,
        TaskExecution.workspace_id == workspace_id))
    if parent is None or execution is None or parent.agent_config_id != agent_id:
        raise ValueError("Parent task run was not found for this agent and workspace.")
    allowed = {"awaiting_clarification"} if clarification else {
        "completed", "rejected", "failed", "stopped"}
    if parent.status not in allowed:
        raise ValueError("Stop or resolve the parent run before starting a new attempt.")
    task = db.scalar(select(SupportTask).where(SupportTask.id == execution.task_id,
        SupportTask.workspace_id == workspace_id).with_for_update()
        .execution_options(populate_existing=True))
    active = db.scalar(select(GraphRun.id).join(TaskExecution,
        TaskExecution.graph_run_id == GraphRun.id).where(TaskExecution.task_id == task.id,
        TaskExecution.workspace_id == workspace_id,
        GraphRun.id != parent_run_id,
        GraphRun.status.in_(["queued", "running", "stopping", "needs_human_review",
                            "awaiting_clarification"])).limit(1))
    if active:
        raise ValueError("Another attempt for this task is still active.")
    previous = db.execute(select(GraphRun.id, GraphRun.status).join(TaskExecution,
        TaskExecution.graph_run_id == GraphRun.id).where(TaskExecution.task_id == task.id,
        TaskExecution.workspace_id == workspace_id).order_by(GraphRun.created_at.desc()).limit(5))
    history = {"task_id": str(task.id), "category": task.category,
        "previous_attempts": [{"run_id": str(id), "status": status} for id, status in previous],
        "internal_note_count": db.scalar(select(func.count()).select_from(TaskNote).where(
            TaskNote.workspace_id == workspace_id, TaskNote.task_id == task.id))}
    if clarification:
        history["clarification"] = {"original_input": task.input_message,
                                     "question": parent.final_answer}
    return task, history
