"""Bounded, workspace-scoped input views over durable tasks and execution attempts."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun
from app.models.task import SupportTask, TaskExecution
from app.schemas.record import RecordDetail, RecordPage, RecordSummary
from app.schemas.record_input import RecordInput


def _records(workspace_id: UUID):
    attempts = select(
        TaskExecution.task_id,
        GraphRun.id.label("latest_run_id"),
        GraphRun.status,
        func.substr(GraphRun.final_answer, 1, 240).label("result_summary"),
        func.count().over(partition_by=TaskExecution.task_id).label("attempt_count"),
        func.row_number().over(partition_by=TaskExecution.task_id,
            order_by=(GraphRun.created_at.desc(), GraphRun.id.desc())).label("position"),
    ).join(GraphRun, GraphRun.id == TaskExecution.graph_run_id).where(
        TaskExecution.workspace_id == workspace_id,
        GraphRun.workspace_id == workspace_id,
    ).subquery()
    return select(
        SupportTask.id, SupportTask.input_message,
        SupportTask.created_at.label("received_at"), SupportTask.created_by_user_id,
        attempts.c.latest_run_id, attempts.c.status, attempts.c.result_summary,
        attempts.c.attempt_count,
    ).join(attempts, attempts.c.task_id == SupportTask.id).where(
        SupportTask.workspace_id == workspace_id, attempts.c.position == 1,
    )


def list_records(db: Session, *, workspace_id: UUID, search: str = "",
                 status: str | None = None, offset: int = 0, limit: int = 20) -> RecordPage:
    statement = _records(workspace_id)
    if search.strip():
        statement = statement.where(SupportTask.input_message.icontains(
            search.strip(), autoescape=True))
    if status:
        statement = statement.where(statement.selected_columns.status == status)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    rows = db.execute(statement.order_by(SupportTask.created_at.desc(), SupportTask.id.desc())
                      .offset(offset).limit(limit)).mappings()
    return RecordPage(items=[RecordSummary.model_validate(row) for row in rows], total=total,
                      offset=offset, limit=limit, has_next=offset + limit < total)


def read_record(db: Session, *, workspace_id: UUID, record_id: UUID) -> RecordDetail | None:
    statement = _records(workspace_id).add_columns(SupportTask.input_envelope_json)
    row = db.execute(statement.where(SupportTask.id == record_id)).mappings().first()
    if row is None:
        return None
    original = (RecordInput.model_validate_json(row["input_envelope_json"])
                if row["input_envelope_json"] else
                RecordInput(content=row["input_message"], source="unknown"))
    return RecordDetail(**RecordSummary.model_validate(row).model_dump(), input=original)
