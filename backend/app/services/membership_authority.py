"""Serialize membership writes and recheck authority under the workspace lock."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


class MembershipAuthorityError(ValueError):
    pass


def lock_workspace(db: Session, workspace_id: UUID) -> None:
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id)
                          .with_for_update().execution_options(populate_existing=True))
    if workspace is None or workspace.deleted_at is not None:
        raise MembershipAuthorityError("Workspace was not found.")


def authorize_membership_change(
    db: Session, *, workspace_id: UUID, actor_user_id: UUID,
    target_user_id: UUID | None = None, new_role: WorkspaceRole | None = None,
) -> None:
    lock_workspace(db, workspace_id)
    workspace = db.get(Workspace, workspace_id)
    if workspace.archived_at is not None:
        raise MembershipAuthorityError("Archived workspaces are read-only.")
    members = list(db.scalars(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id.in_([actor_user_id, target_user_id or actor_user_id]),
    ).execution_options(populate_existing=True)))
    actor = next((m for m in members if m.user_id == actor_user_id), None)
    target = next((m for m in members if m.user_id == target_user_id), None)
    if actor is None:
        raise MembershipAuthorityError("Workspace membership is required.")
    if actor.role == WorkspaceRole.owner:
        return
    lower = {WorkspaceRole.viewer, WorkspaceRole.operator}
    if (actor.role != WorkspaceRole.admin or target_user_id == actor_user_id
            or (target is not None and target.role not in lower)
            or (new_role is not None and new_role not in lower)):
        raise MembershipAuthorityError("Admins can manage only Viewer and Operator memberships.")
