from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_owner
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.folder import (
    ResourceFolderCreateRequest,
    ResourceFolderResponse,
    ResourceFolderUpdateRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.folder_service import (
    ResourceFolderError,
    ResourceFolderInvalidTypeError,
    ResourceFolderNotEmptyError,
    ResourceFolderNotFoundError,
    ResourceFolderService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}/resource-folders", tags=["resource-folders"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
WorkspaceOwnerAccess = Annotated[Workspace, Depends(require_workspace_owner)]
FolderId = Annotated[UUID, Path()]


@router.get("", response_model=list[ResourceFolderResponse])
def list_resource_folders(
    resource_type: Annotated[str, Query(min_length=1, max_length=40)],
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> list[ResourceFolderResponse]:
    try:
        folders = ResourceFolderService(db).list_folders(
            workspace_id=workspace.id, resource_type=resource_type
        )
    except ResourceFolderInvalidTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "resource_folder_invalid_type", "message": str(exc)},
        ) from exc
    return [ResourceFolderResponse.model_validate(folder) for folder in folders]


@router.post("", response_model=ResourceFolderResponse, status_code=status.HTTP_201_CREATED)
def create_resource_folder(
    payload: ResourceFolderCreateRequest,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ResourceFolderResponse:
    try:
        folder = ResourceFolderService(db).create_folder(
            workspace_id=workspace.id,
            resource_type=payload.resource_type,
            name=payload.name,
            parent_folder_id=payload.parent_folder_id,
            current_user=current_user,
        )
    except ResourceFolderNotFoundError as exc:
        raise _not_found(exc) from exc
    except ResourceFolderError as exc:
        raise _bad_request(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="resource_folder.created",
        resource_type="resource_folder",
        resource_id=folder.id,
        metadata={"name": folder.name, "resource_type": folder.resource_type},
    )
    return ResourceFolderResponse.model_validate(folder)


@router.patch("/{folder_id}", response_model=ResourceFolderResponse)
def update_resource_folder(
    folder_id: FolderId,
    payload: ResourceFolderUpdateRequest,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ResourceFolderResponse:
    try:
        folder = ResourceFolderService(db).update_folder(
            workspace_id=workspace.id,
            folder_id=folder_id,
            name=payload.name,
            parent_folder_id=payload.parent_folder_id,
        )
    except ResourceFolderNotFoundError as exc:
        raise _not_found(exc) from exc
    except ResourceFolderError as exc:
        raise _bad_request(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="resource_folder.updated",
        resource_type="resource_folder",
        resource_id=folder.id,
        metadata={"name": folder.name, "resource_type": folder.resource_type},
    )
    return ResourceFolderResponse.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource_folder(
    folder_id: FolderId,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        ResourceFolderService(db).delete_folder(workspace_id=workspace.id, folder_id=folder_id)
    except ResourceFolderNotFoundError as exc:
        raise _not_found(exc) from exc
    except ResourceFolderNotEmptyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "resource_folder_not_empty", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="resource_folder.deleted",
        resource_type="resource_folder",
        resource_id=folder_id,
    )


def _not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "resource_folder_not_found", "message": "Resource folder was not found."},
    )


def _bad_request(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "resource_folder_invalid", "message": str(exc)},
    )
