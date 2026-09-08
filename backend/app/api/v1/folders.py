from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.folder import (
    ResourceFolderCountResponse,
    ResourceFolderCountSummaryResponse,
    ResourceFolderCreateRequest,
    ResourceFolderResponse,
    ResourceFolderUpdateRequest,
)
from app.services.folder_service import (
    ResourceFolderError,
    ResourceFolderInvalidTypeError,
    ResourceFolderNotEmptyError,
    ResourceFolderNotFoundError,
    ResourceFolderService,
)
from app.services.workspace_service import WorkspaceService, permissions_for_role

router = APIRouter(prefix="/workspaces/{workspace_id}/resource-folders", tags=["resource-folders"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
ResourceFolderManageAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resource_folders:manage"))
]
FolderId = Annotated[UUID, Path()]

FOLDER_READ_PERMISSIONS = {
    "knowledge_document": "knowledge:read",
    "dataset": "data:read",
    "evaluation_run": "evaluations:read",
    "agent_config": "agents:read",
}


@router.get("", response_model=list[ResourceFolderResponse])
def list_resource_folders(
    resource_type: Annotated[str, Query(min_length=1, max_length=40)],
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> list[ResourceFolderResponse]:
    _require_resource_folder_read(
        resource_type=resource_type,
        workspace=workspace,
        current_user=current_user,
        db=db,
    )
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


@router.get("/counts", response_model=ResourceFolderCountSummaryResponse)
def get_resource_folder_counts(
    resource_type: Annotated[str, Query(min_length=1, max_length=40)],
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ResourceFolderCountSummaryResponse:
    _require_resource_folder_read(
        resource_type=resource_type,
        workspace=workspace,
        current_user=current_user,
        db=db,
    )
    try:
        summary = ResourceFolderService(db).count_resources(
            workspace_id=workspace.id, resource_type=resource_type
        )
    except ResourceFolderInvalidTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "resource_folder_invalid_type", "message": str(exc)},
        ) from exc
    return ResourceFolderCountSummaryResponse(
        resource_type=summary.resource_type,
        total_count=summary.total_count,
        unfiled_count=summary.unfiled_count,
        folder_counts=[
            ResourceFolderCountResponse(folder_id=folder_id, resource_count=count)
            for folder_id, count in sorted(
                summary.folder_counts.items(), key=lambda item: str(item[0])
            )
        ],
    )


@router.post("", response_model=ResourceFolderResponse, status_code=status.HTTP_201_CREATED)
def create_resource_folder(
    payload: ResourceFolderCreateRequest,
    workspace: ResourceFolderManageAccess,
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
    return ResourceFolderResponse.model_validate(folder)


@router.patch("/{folder_id}", response_model=ResourceFolderResponse)
def update_resource_folder(
    folder_id: FolderId,
    payload: ResourceFolderUpdateRequest,
    workspace: ResourceFolderManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ResourceFolderResponse:
    try:
        folder = ResourceFolderService(db).update_folder(
            workspace_id=workspace.id,
            folder_id=folder_id,
            name=payload.name,
            parent_folder_id=payload.parent_folder_id,
            update_parent="parent_folder_id" in payload.model_fields_set,
            actor_user_id=current_user.id,
        )
    except ResourceFolderNotFoundError as exc:
        raise _not_found(exc) from exc
    except ResourceFolderError as exc:
        raise _bad_request(exc) from exc
    return ResourceFolderResponse.model_validate(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource_folder(
    folder_id: FolderId,
    workspace: ResourceFolderManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        ResourceFolderService(db).delete_folder(
            workspace_id=workspace.id, folder_id=folder_id, actor_user_id=current_user.id,
        )
    except ResourceFolderNotFoundError as exc:
        raise _not_found(exc) from exc
    except ResourceFolderNotEmptyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "resource_folder_not_empty", "message": str(exc)},
        ) from exc


def _require_resource_folder_read(
    *,
    resource_type: str,
    workspace: Workspace,
    current_user: User,
    db: Session,
) -> None:
    required_permission = FOLDER_READ_PERMISSIONS.get(resource_type)
    if required_permission is None:
        return
    membership = WorkspaceService(db).get_membership(workspace.id, current_user.id)
    permissions = permissions_for_role(membership.role) if membership else []
    if required_permission in permissions or "resource_folders:manage" in permissions:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "workspace_permission_required",
            "message": f"This action requires {required_permission} permission.",
            "required_permission": required_permission,
        },
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
