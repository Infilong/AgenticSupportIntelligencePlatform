from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query

from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.support import attempts, reading, service
from app.modules.support.projections import HandoffExport
from app.modules.support.schemas import (
    DevelopmentResponse,
    MessageCreated,
    MessageInput,
    MessagePage,
    RunDetail,
)

router = APIRouter(prefix="/api/workspaces/{workspace_id}", tags=["support"])


@router.post("/runs/{run_id}/attempts", status_code=202, response_model=MessageCreated)
def create_attempt(
    workspace_id: UUID,
    run_id: UUID,
    data: attempts.AttemptInput,
    user: CurrentUser,
    db: Database,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)],
):
    result = attempts.create(db, workspace_id, user.id, run_id, key, data)
    db.commit()
    return result


@router.post("/messages", status_code=202, response_model=MessageCreated)
def create_message(
    workspace_id: UUID,
    data: MessageInput,
    user: CurrentUser,
    db: Database,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)],
):
    result = service.create_message(db, workspace_id, user.id, data, key)
    db.commit()
    return result


@router.get("/messages", response_model=MessagePage)
def list_messages(
    workspace_id: UUID,
    user: CurrentUser,
    db: Database,
    search: str = Query("", max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=50),
):
    return reading.messages(db, workspace_id, user.id, search, offset, limit)


@router.get("/runs/{run_id}", response_model=RunDetail)
def run_detail(workspace_id: UUID, run_id: UUID, user: CurrentUser, db: Database):
    return reading.detail(db, workspace_id, user.id, run_id)


@router.post("/runs/{run_id}/cancel", response_model=RunDetail)
def cancel(workspace_id: UUID, run_id: UUID, user: CurrentUser, db: Database):
    service.cancel_run(db, workspace_id, user.id, run_id)
    db.commit()
    return reading.detail(db, workspace_id, user.id, run_id)


@router.get("/runs/{run_id}/development-handoff", response_model=HandoffExport)
def export(workspace_id: UUID, run_id: UUID, user: CurrentUser, db: Database):
    return reading.export_handoff(db, workspace_id, user.id, run_id)


@router.post("/runs/{run_id}/development-handoff/{handoff_id}", status_code=202, response_model=RunDetail)
def contribute(
    workspace_id: UUID,
    run_id: UUID,
    handoff_id: UUID,
    data: DevelopmentResponse,
    user: CurrentUser,
    db: Database,
):
    service.submit_response(db, workspace_id, user.id, run_id, handoff_id, data)
    db.commit()
    return reading.detail(db, workspace_id, user.id, run_id)
