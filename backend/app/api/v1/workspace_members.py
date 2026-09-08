from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import (
    require_workspace_member,
    require_workspace_owner,
    require_workspace_permission,
)
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import (
    WorkspaceMemberAddRequest,
    WorkspaceMemberResponse,
    WorkspaceMemberRoleUpdateRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.workspace_service import (
    WorkspaceMemberAlreadyExistsError,
    WorkspaceMemberNotFoundError,
    WorkspaceMemberOwnerError,
    WorkspaceMemberUserNotFoundError,
    WorkspaceService,
    permissions_for_role,
)

router = APIRouter(tags=["workspaces"])
CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
WorkspaceOwnerAccess = Annotated[Workspace, Depends(require_workspace_owner)]
MemberReadAccess = Annotated[Workspace, Depends(require_workspace_permission("members:read"))]
MemberManageAccess = Annotated[Workspace, Depends(require_workspace_permission("members:manage"))]
MemberUserId = Annotated[UUID, Path()]


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
def list_workspace_members(
    workspace: MemberReadAccess, db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str, Query(max_length=160)] = "",
) -> list[WorkspaceMemberResponse]:
    members = WorkspaceService(db).list_members(workspace_id=workspace.id,
                                                limit=limit, offset=offset, search=search)
    return [_member_response(member) for member in members]


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_workspace_member(
    payload: WorkspaceMemberAddRequest,
    workspace: MemberManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceMemberResponse:
    _reject_archived_workspace_mutation(workspace)
    service = WorkspaceService(db)
    try:
        member = service.add_member_by_email(
            workspace_id=workspace.id, email=payload.email, role=payload.role,
            actor_user_id=current_user.id
        )
    except WorkspaceMemberOwnerError as exc:
        raise _member_owner_error(exc) from exc
    except WorkspaceMemberUserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "workspace_member_user_not_found",
                "message": "User must register before joining a workspace.",
            },
        ) from exc
    except WorkspaceMemberAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "workspace_member_already_exists",
                "message": "User is already a workspace member.",
            },
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="workspace_member.added",
        resource_type="workspace_member",
        resource_id=member.id,
        metadata={
            "user_id": str(member.user_id),
            "email": member.user.email if member.user else payload.email,
            "role": member.role,
        },
    )
    return _member_response(member)


@router.patch("/{workspace_id}/members/{member_user_id}", response_model=WorkspaceMemberResponse)
def update_workspace_member_role(
    member_user_id: MemberUserId,
    payload: WorkspaceMemberRoleUpdateRequest,
    workspace: MemberManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> WorkspaceMemberResponse:
    _reject_archived_workspace_mutation(workspace)
    service = WorkspaceService(db)
    try:
        member = service.update_member_role(
            workspace_id=workspace.id,
            user_id=member_user_id,
            role=payload.role,
            actor_user_id=current_user.id,
        )
    except WorkspaceMemberNotFoundError as exc:
        raise _member_not_found(exc) from exc
    except WorkspaceMemberOwnerError as exc:
        raise _member_owner_error(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="workspace_member.role_updated",
        resource_type="workspace_member",
        resource_id=member.id,
        metadata={"user_id": str(member.user_id), "role": member.role},
    )
    return _member_response(member)


@router.delete("/{workspace_id}/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_workspace_member(
    member_user_id: MemberUserId,
    workspace: MemberManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    _reject_archived_workspace_mutation(workspace)
    service = WorkspaceService(db)
    member = service.get_membership(workspace.id, member_user_id)
    try:
        service.remove_member(
            workspace_id=workspace.id, user_id=member_user_id, actor_user_id=current_user.id
        )
    except WorkspaceMemberNotFoundError as exc:
        raise _member_not_found(exc) from exc
    except WorkspaceMemberOwnerError as exc:
        raise _member_owner_error(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="workspace_member.removed",
        resource_type="workspace_member",
        resource_id=member.id if member else member_user_id,
        metadata={"user_id": str(member_user_id)},
    )


def _reject_archived_workspace_mutation(workspace: Workspace) -> None:
    if workspace.archived_at is None:
        return
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "workspace_archived",
            "message": (
                "Archived workspaces are read-only. "
                "Restore the workspace before changing workspace settings."
            ),
        },
    )


def _member_response(member: WorkspaceMember) -> WorkspaceMemberResponse:
    permissions = permissions_for_role(member.role)
    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        email=member.user.email if member.user else "unknown",
        display_name=member.user.display_name if member.user else "Unknown user",
        role=member.role,
        permissions=permissions,
        created_at=member.created_at,
    )


def _member_not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "workspace_member_not_found", "message": "Workspace member was not found."},
    )


def _member_owner_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": "workspace_owner_guard", "message": str(exc)},
    )
