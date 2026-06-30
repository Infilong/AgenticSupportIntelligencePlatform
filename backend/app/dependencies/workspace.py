from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceRole
from app.services.workspace_service import (
    ARCHIVED_WORKSPACE_ALLOWED_PERMISSIONS,
    WorkspaceService,
    permissions_for_role,
)

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


def require_workspace_owner(
    workspace_id: WorkspaceId,
    current_user: CurrentUser,
    db: DbSession,
) -> Workspace:
    service = WorkspaceService(db)
    workspace = service.get_for_member(workspace_id, current_user.id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "workspace_not_found", "message": "Workspace was not found."},
        )
    membership = service.get_membership(workspace_id, current_user.id)
    if membership is None or membership.role != WorkspaceRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "workspace_owner_required",
                "message": "This action requires workspace owner permission.",
            },
        )
    return workspace


def require_workspace_permission(
    permission: str,
) -> Callable[[WorkspaceId, CurrentUser, DbSession], Workspace]:
    def dependency(
        workspace_id: WorkspaceId,
        current_user: CurrentUser,
        db: DbSession,
    ) -> Workspace:
        service = WorkspaceService(db)
        workspace = service.get_for_member(workspace_id, current_user.id)
        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "workspace_not_found", "message": "Workspace was not found."},
            )
        membership = service.get_membership(workspace_id, current_user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "workspace_not_found", "message": "Workspace was not found."},
            )
        permissions = permissions_for_role(membership.role)
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "workspace_permission_required",
                    "message": f"This action requires {permission} permission.",
                    "required_permission": permission,
                },
            )
        archived_write_blocked = (
            workspace.archived_at is not None
            and permission not in ARCHIVED_WORKSPACE_ALLOWED_PERMISSIONS
        )
        if archived_write_blocked:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "workspace_archived",
                    "message": (
                        "Archived workspaces are read-only. "
                        "Restore the workspace before changing resources."
                    ),
                    "required_permission": permission,
                },
            )
        return workspace

    return dependency
