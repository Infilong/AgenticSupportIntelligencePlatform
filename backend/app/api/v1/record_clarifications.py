"""Submit additional input under the original record, never as privileged instructions."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.v1.records import Actor, Db, RunAccess
from app.models.agent import GraphRun
from app.models.task import TaskExecution
from app.schemas.record import RecordDetail
from app.schemas.record_input import RecordClarificationRequest
from app.services.record_queries import read_record
from app.services.task_admission import TaskAdmissionError, admit_task

router = APIRouter(prefix="/workspaces/{workspace_id}/records", tags=["records"])


@router.post("/{record_id}/clarifications", response_model=RecordDetail, status_code=202)
def clarify_record(record_id: UUID, payload: RecordClarificationRequest,
                   workspace: RunAccess, actor: Actor, db: Db):
    parent = db.scalar(select(GraphRun).join(TaskExecution,
        TaskExecution.graph_run_id == GraphRun.id).where(
        GraphRun.workspace_id == workspace.id, GraphRun.id == payload.run_id,
        TaskExecution.workspace_id == workspace.id, TaskExecution.task_id == record_id))
    if parent is None:
        raise HTTPException(404, detail="Record attempt not found.")
    try:
        task, _ = admit_task(db, workspace_id=workspace.id, user_id=actor.id,
            agent_id=parent.agent_config_id, message=payload.reply, language=parent.language,
            request_key=payload.request_key, parent_run_id=parent.id,
            clarification_reply=payload.reply)
    except TaskAdmissionError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "clarification_failed",
                                         "message": str(error)}) from error
    return read_record(db, workspace_id=workspace.id, record_id=task.id)
