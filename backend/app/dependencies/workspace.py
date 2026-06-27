from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.services.workspace_service import WorkspaceService

WorkspaceId = Annotated[UUID, Path()]
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


def require_workspace_member(
    workspace_id: WorkspaceId,
    current_user: CurrentUser,
    db: DbSession,
) -> Workspace:
    workspace = WorkspaceService(db).get_for_member(workspace_id, current_user.id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "workspace_not_found", "message": "Workspace was not found."},
        )
    return workspace
