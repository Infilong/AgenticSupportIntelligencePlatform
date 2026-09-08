from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import normalize_email
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.membership_authority import (
    MembershipAuthorityError,
    authorize_membership_change,
    lock_workspace,
)
from app.services.workspace_permissions import (
    ARCHIVED_WORKSPACE_ALLOWED_PERMISSIONS as ARCHIVED_WORKSPACE_ALLOWED_PERMISSIONS,
)
from app.services.workspace_permissions import (
    ROLE_PERMISSIONS as ROLE_PERMISSIONS,
)


class WorkspaceMemberError(ValueError):
    pass


class WorkspaceMemberUserNotFoundError(WorkspaceMemberError):
    pass


class WorkspaceMemberAlreadyExistsError(WorkspaceMemberError):
    pass


class WorkspaceMemberNotFoundError(WorkspaceMemberError):
    pass


WorkspaceMemberOwnerError = MembershipAuthorityError


class WorkspaceNameConflictError(ValueError):
    pass


class WorkspaceDeleteConfirmationError(ValueError):
    pass


def permissions_for_role(role: WorkspaceRole) -> list[str]:
    return ROLE_PERMISSIONS.get(role, []).copy()


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db

    def create_workspace(self, *, name: str, creator: User) -> Workspace:
        resolved_name = name.strip()
        if self._workspace_name_exists_for_user(user_id=creator.id, name=resolved_name):
            raise WorkspaceNameConflictError("Workspace name already exists for your account.")
        workspace = Workspace(name=resolved_name, created_by_user_id=creator.id)
        self.db.add(workspace)
        self.db.flush()
        self.db.add(
            WorkspaceMember(workspace_id=workspace.id, user_id=creator.id, role=WorkspaceRole.owner)
        )
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def list_for_user(self, user_id: UUID) -> list[Workspace]:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id, Workspace.deleted_at.is_(None))
            .order_by(Workspace.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_for_member(self, workspace_id: UUID, user_id: UUID) -> Workspace | None:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                Workspace.id == workspace_id,
                WorkspaceMember.user_id == user_id,
                Workspace.deleted_at.is_(None),
            )
        )
        return self.db.scalar(statement)

    def get_membership(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        statement = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        return self.db.scalar(statement)

    def update_workspace_name(
        self, *, workspace: Workspace, name: str, actor_user_id: UUID
    ) -> Workspace:
        resolved_name = name.strip()
        if self._workspace_name_exists_for_user(
            user_id=actor_user_id, name=resolved_name, exclude_workspace_id=workspace.id
        ):
            raise WorkspaceNameConflictError("Workspace name already exists for your account.")
        workspace.name = resolved_name
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def archive_workspace(self, *, workspace: Workspace) -> Workspace:
        if workspace.archived_at is None:
            workspace.archived_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(workspace)
        return workspace

    def restore_workspace(self, *, workspace: Workspace) -> Workspace:
        if workspace.archived_at is not None:
            workspace.archived_at = None
            self.db.commit()
            self.db.refresh(workspace)
        return workspace

    def delete_workspace(self, *, workspace: Workspace, confirmation_name: str) -> Workspace:
        if confirmation_name.strip() != workspace.name:
            raise WorkspaceDeleteConfirmationError("Workspace name confirmation did not match.")
        if workspace.deleted_at is None:
            workspace.deleted_at = datetime.now(UTC)
            self.db.commit()
            self.db.refresh(workspace)
        return workspace

    def leave_workspace(self, *, workspace_id: UUID, user_id: UUID) -> None:
        lock_workspace(self.db, workspace_id)
        self.db.expire_all()
        membership = self.get_membership(workspace_id, user_id)
        if membership is None:
            raise WorkspaceMemberNotFoundError("Workspace member was not found.")
        if membership.role == WorkspaceRole.owner:
            self._require_another_owner(workspace_id=workspace_id, user_id=user_id)
        self.db.delete(membership)
        self.db.commit()

    def _workspace_name_exists_for_user(
        self, *, user_id: UUID, name: str, exclude_workspace_id: UUID | None = None
    ) -> bool:
        normalized_name = name.strip().lower()
        statement = (
            select(Workspace.id)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(
                WorkspaceMember.user_id == user_id,
                func.lower(Workspace.name) == normalized_name,
                Workspace.deleted_at.is_(None),
            )
        )
        if exclude_workspace_id is not None:
            statement = statement.where(Workspace.id != exclude_workspace_id)
        return self.db.scalar(statement.limit(1)) is not None

    def list_members(self, *, workspace_id: UUID, limit: int = 20,
                     offset: int = 0, search: str = "") -> list[WorkspaceMember]:
        statement = (
            select(WorkspaceMember)
            .join(User, User.id == WorkspaceMember.user_id)
            .options(joinedload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.created_at.asc())
            .limit(limit).offset(offset)
        )
        if search.strip():
            pattern = f"%{search.strip()}%"
            statement = statement.where(or_(User.email.ilike(pattern),
                                            User.display_name.ilike(pattern)))
        return list(self.db.scalars(statement).all())

    def add_member_by_email(
        self, *, workspace_id: UUID, email: str, actor_user_id: UUID,
        role: WorkspaceRole = WorkspaceRole.viewer,
    ) -> WorkspaceMember:
        authorize_membership_change(self.db, workspace_id=workspace_id,
                                    actor_user_id=actor_user_id, new_role=role)
        user = self.db.scalar(select(User).where(User.email == normalize_email(email)))
        if user is None:
            raise WorkspaceMemberUserNotFoundError("User must register before joining a workspace.")
        existing = self.get_membership(workspace_id, user.id)
        if existing is not None:
            raise WorkspaceMemberAlreadyExistsError("User is already a workspace member.")
        membership = WorkspaceMember(workspace_id=workspace_id, user_id=user.id, role=role)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return self._refresh_member_user(membership)

    def update_member_role(
        self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole, actor_user_id: UUID
    ) -> WorkspaceMember:
        authorize_membership_change(self.db, workspace_id=workspace_id,
            actor_user_id=actor_user_id, target_user_id=user_id, new_role=role)
        membership = self.get_membership(workspace_id, user_id)
        if membership is None:
            raise WorkspaceMemberNotFoundError("Workspace member was not found.")
        is_self_demote = (
            user_id == actor_user_id
            and membership.role == WorkspaceRole.owner
            and role != WorkspaceRole.owner
        )
        if is_self_demote:
            raise WorkspaceMemberOwnerError("Owners cannot demote their own membership.")
        if membership.role == WorkspaceRole.owner and role != WorkspaceRole.owner:
            self._require_another_owner(workspace_id=workspace_id, user_id=user_id)
        membership.role = role
        self.db.commit()
        self.db.refresh(membership)
        return self._refresh_member_user(membership)

    def remove_member(self, *, workspace_id: UUID, user_id: UUID, actor_user_id: UUID) -> None:
        authorize_membership_change(self.db, workspace_id=workspace_id,
                                    actor_user_id=actor_user_id, target_user_id=user_id)
        membership = self.get_membership(workspace_id, user_id)
        if membership is None:
            raise WorkspaceMemberNotFoundError("Workspace member was not found.")
        if user_id == actor_user_id:
            raise WorkspaceMemberOwnerError("Owners cannot remove their own membership.")
        if membership.role == WorkspaceRole.owner:
            self._require_another_owner(workspace_id=workspace_id, user_id=user_id)
        self.db.delete(membership)
        self.db.commit()

    def _require_another_owner(self, *, workspace_id: UUID, user_id: UUID) -> None:
        owner_count = self.db.scalar(
            select(func.count())
            .select_from(WorkspaceMember)
            .where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.role == WorkspaceRole.owner,
                WorkspaceMember.user_id != user_id,
            )
        )
        if not owner_count:
            raise WorkspaceMemberOwnerError("Workspace must keep at least one owner.")

    def _refresh_member_user(self, membership: WorkspaceMember) -> WorkspaceMember:
        refreshed = self.db.scalar(
            select(WorkspaceMember)
            .options(joinedload(WorkspaceMember.user))
            .where(WorkspaceMember.id == membership.id)
        )
        return refreshed if refreshed is not None else membership
