from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceCreateRequest, WorkspaceResponse
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(current_user: CurrentUser, db: DbSession) -> list[WorkspaceResponse]:
    service = WorkspaceService(db)
    workspaces = service.list_for_user(current_user.id)
    return [WorkspaceResponse.model_validate(workspace) for workspace in workspaces]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceResponse:
    service = WorkspaceService(db)
    workspace = service.create_workspace(name=payload.name, creator=current_user)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace: WorkspaceMemberAccess) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(workspace)
