"""Records expose persisted inputs rather than duplicating their retry attempts."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.agent import GraphRunStatus
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.record import RecordDetail, RecordPage
from app.schemas.record_input import RecordCreateRequest
from app.services.record_queries import list_records, read_record
from app.services.task_admission import TaskAdmissionError, admit_task

router = APIRouter(prefix="/workspaces/{workspace_id}/records", tags=["records"])
Db = Annotated[Session, Depends(get_db)]
ReadAccess = Annotated[Workspace, Depends(require_workspace_permission("traces:read"))]
RunAccess = Annotated[Workspace, Depends(require_workspace_permission("agents:run"))]
Actor = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=RecordDetail, status_code=202)
def create_record(payload: RecordCreateRequest, workspace: RunAccess, actor: Actor, db: Db):
    try:
        task, _ = admit_task(db, workspace_id=workspace.id, user_id=actor.id,
            agent_id=payload.agent_id, message=payload.input.processing_text(),
            request_key=payload.request_key, language=payload.language, record_input=payload.input)
    except TaskAdmissionError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "record_admission_failed",
                                         "message": str(error)}) from error
    return read_record(db, workspace_id=workspace.id, record_id=task.id)


@router.get("", response_model=RecordPage)
def records(workspace: ReadAccess, db: Db,
            search: Annotated[str, Query(max_length=200)] = "",
            status: GraphRunStatus | None = None,
            offset: Annotated[int, Query(ge=0)] = 0,
            limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return list_records(db, workspace_id=workspace.id, search=search,
                        status=status, offset=offset, limit=limit)


@router.get("/{record_id}", response_model=RecordDetail)
def record(record_id: UUID, workspace: ReadAccess, db: Db):
    result = read_record(db, workspace_id=workspace.id, record_id=record_id)
    if result is None:
        raise HTTPException(404, detail="Record not found.")
    return result
