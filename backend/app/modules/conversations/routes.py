from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Header, UploadFile

from app.jobs.queue import authorize
from app.modules.conversations import service
from app.modules.conversations.schemas import ImportResult, Labels, SavedMessage
from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.support.schemas import MessageCreated

router = APIRouter(prefix="/api/workspaces/{workspace_id}", tags=["conversations"])


@router.post("/message-imports", status_code=201, response_model=ImportResult)
def import_messages(
    workspace_id: UUID,
    user: CurrentUser,
    db: Database,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)],
    file: UploadFile = File(...),
):
    authorize(db, workspace_id, user.id)
    batch = service.import_messages(
        db, workspace_id, user.id, file.filename, file.file.read(service.MAX_BYTES + 1), key
    )
    result = {"id": batch.id, "filename": batch.filename, "message_count": batch.message_count}
    db.commit()
    return result


@router.get("/messages/{message_id}", response_model=SavedMessage)
def detail(workspace_id: UUID, message_id: UUID, user: CurrentUser, db: Database):
    return service.detail(db, workspace_id, user.id, message_id)


@router.put("/messages/{message_id}/labels", response_model=SavedMessage)
def labels(workspace_id: UUID, message_id: UUID, data: Labels, user: CurrentUser, db: Database):
    authorize(db, workspace_id, user.id)
    message = service.get_message(db, workspace_id, message_id)
    message.labels = data.labels
    db.commit()
    return service.detail(db, workspace_id, user.id, message_id)


@router.post("/messages/{message_id}/process", status_code=202, response_model=MessageCreated)
def start(workspace_id: UUID, message_id: UUID, user: CurrentUser, db: Database):
    result = service.start(db, workspace_id, user.id, message_id)
    db.commit()
    return result
