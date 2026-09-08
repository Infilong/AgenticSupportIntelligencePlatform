from typing import Annotated, get_args
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.v1.workspace_members import (
    _member_not_found,
    _member_owner_error,
    _reject_archived_workspace_mutation,
)
from app.api.v1.workspace_members import (
    router as members_router,
)
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import (
    require_workspace_member,
    require_workspace_owner,
    require_workspace_permission,
)
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    AssignableRole,
    WorkspaceCreateRequest,
    WorkspaceDeleteRequest,
    WorkspaceMembershipResponse,
    WorkspacePermissionMatrixEntry,
    WorkspacePermissionMatrixResponse,
    WorkspaceResponse,
    WorkspaceUpdateRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.workspace_service import (
    ROLE_PERMISSIONS,
    WorkspaceDeleteConfirmationError,
    WorkspaceMemberNotFoundError,
    WorkspaceMemberOwnerError,
    WorkspaceNameConflictError,
    WorkspaceService,
    permissions_for_role,
)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
router.include_router(members_router)
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
WorkspaceOwnerAccess = Annotated[Workspace, Depends(require_workspace_owner)]
MemberReadAccess = Annotated[Workspace, Depends(require_workspace_permission("members:read"))]
MemberUserId = Annotated[UUID, Path()]


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
    try:
        workspace = service.create_workspace(name=payload.name, creator=current_user)
    except WorkspaceNameConflictError as exc:
        raise _workspace_name_conflict(exc) from exc
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace: WorkspaceMemberAccess) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace_settings(
    payload: WorkspaceUpdateRequest,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceResponse:
    _reject_archived_workspace_mutation(workspace)
    try:
        updated = WorkspaceService(db).update_workspace_name(
            workspace=workspace, name=payload.name, actor_user_id=current_user.id
        )
    except WorkspaceNameConflictError as exc:
        raise _workspace_name_conflict(exc) from exc
    AuditLogService(db).record(
        workspace_id=updated.id,
        actor_user_id=current_user.id,
        action="workspace.updated",
        resource_type="workspace",
        resource_id=updated.id,
        metadata={"name": updated.name},
    )
    return WorkspaceResponse.model_validate(updated)


@router.post("/{workspace_id}/archive", response_model=WorkspaceResponse)
def archive_workspace(
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceResponse:
    archived = WorkspaceService(db).archive_workspace(workspace=workspace)
    AuditLogService(db).record(
        workspace_id=archived.id,
        actor_user_id=current_user.id,
        action="workspace.archived",
        resource_type="workspace",
        resource_id=archived.id,
        metadata={"name": archived.name},
    )
    return WorkspaceResponse.model_validate(archived)


@router.post("/{workspace_id}/restore", response_model=WorkspaceResponse)
def restore_workspace(
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceResponse:
    restored = WorkspaceService(db).restore_workspace(workspace=workspace)
    AuditLogService(db).record(
        workspace_id=restored.id,
        actor_user_id=current_user.id,
        action="workspace.restored",
        resource_type="workspace",
        resource_id=restored.id,
        metadata={"name": restored.name},
    )
    return WorkspaceResponse.model_validate(restored)


@router.post("/{workspace_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_workspace(
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        WorkspaceService(db).leave_workspace(workspace_id=workspace.id, user_id=current_user.id)
        AuditLogService(db).record(
            workspace_id=workspace.id,
            actor_user_id=current_user.id,
            action="workspace_member.left",
            resource_type="workspace_member",
            resource_id=current_user.id,
            metadata={"user_id": str(current_user.id)},
        )
    except WorkspaceMemberNotFoundError as exc:
        raise _member_not_found(exc) from exc
    except WorkspaceMemberOwnerError as exc:
        raise _member_owner_error(exc) from exc


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    payload: WorkspaceDeleteRequest,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    service = WorkspaceService(db)
    try:
        if payload.confirmation_name.strip() != workspace.name:
            raise WorkspaceDeleteConfirmationError("Workspace name confirmation did not match.")
        AuditLogService(db).record(
            workspace_id=workspace.id,
            actor_user_id=current_user.id,
            action="workspace.deleted",
            resource_type="workspace",
            resource_id=workspace.id,
            metadata={"name": workspace.name, "mode": "soft_delete"},
        )
        service.delete_workspace(
            workspace=workspace,
            confirmation_name=payload.confirmation_name,
        )
    except WorkspaceDeleteConfirmationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "workspace_delete_confirmation_mismatch", "message": str(exc)},
        ) from exc


@router.get("/{workspace_id}/permission-matrix", response_model=WorkspacePermissionMatrixResponse)
def get_permission_matrix(workspace: WorkspaceMemberAccess) -> WorkspacePermissionMatrixResponse:
    return WorkspacePermissionMatrixResponse(
        roles=[
            WorkspacePermissionMatrixEntry(role=role, permissions=permissions.copy())
            for role, permissions in ROLE_PERMISSIONS.items() if role in get_args(AssignableRole)
        ]
    )


@router.get("/{workspace_id}/membership", response_model=WorkspaceMembershipResponse)
def get_workspace_membership(
    workspace: WorkspaceMemberAccess, current_user: CurrentUser, db: DbSession
) -> WorkspaceMembershipResponse:
    membership = WorkspaceService(db).get_membership(workspace.id, current_user.id)
    if membership is None:
        # `require_workspace_member` already proves membership; this guards a deletion race.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "workspace_not_found", "message": "Workspace was not found."},
        )
    permissions = permissions_for_role(membership.role)
    return WorkspaceMembershipResponse(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=membership.role,
        permissions=permissions,
        can_manage_resources="resources:delete" in permissions,
        can_manage_workspace="workspace:manage" in permissions,
    )


def _workspace_name_conflict(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "workspace_name_conflict", "message": str(exc)},
    )
