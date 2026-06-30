from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.security import normalize_email
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole

BASE_PERMISSIONS = [
    "workspace:read",
    "tasks:read",
    "settings:read",
]

VIEWER_PERMISSIONS = [
    *BASE_PERMISSIONS,
    "data:read",
    "knowledge:read",
    "agents:read",
    "traces:read",
    "reviews:read",
    "evaluations:read",
    "costs:read",
]

REVIEWER_PERMISSIONS = [
    *BASE_PERMISSIONS,
    "knowledge:read",
    "agents:read",
    "traces:read",
    "reviews:read",
    "costs:read",
    "reviews:resolve",
]

DEVELOPER_PERMISSIONS = [
    *VIEWER_PERMISSIONS,
    "tools:read",
    "guardrails:read",
    "prompts:read",
    "models:read",
    "system:read",
    "data:write",
    "knowledge:write",
    "agents:run",
    "agents:configure",
    "tools:configure",
    "evaluations:run",
    "prompts:write",
    "resource_folders:manage",
]

MEMBER_PERMISSIONS = [
    *VIEWER_PERMISSIONS,
    "tools:read",
    "guardrails:read",
    "system:read",
    "data:write",
    "knowledge:write",
    "agents:run",
    "agents:configure",
    "reviews:resolve",
    "evaluations:run",
]

OWNER_PERMISSIONS = [
    *DEVELOPER_PERMISSIONS,
    "reviews:resolve",
    "members:read",
    "audit:read",
    "budget_policy:read",
    "workspace:manage",
    "resources:delete",
    "agents:delete",
    "models:write",
    "guardrails:configure",
    "budget_policy:manage",
]

ROLE_PERMISSIONS = {
    WorkspaceRole.owner: OWNER_PERMISSIONS,
    WorkspaceRole.developer: DEVELOPER_PERMISSIONS,
    WorkspaceRole.member: MEMBER_PERMISSIONS,
    WorkspaceRole.reviewer: REVIEWER_PERMISSIONS,
    WorkspaceRole.viewer: VIEWER_PERMISSIONS,
}


class WorkspaceMemberError(ValueError):
    pass


class WorkspaceMemberUserNotFoundError(WorkspaceMemberError):
    pass


class WorkspaceMemberAlreadyExistsError(WorkspaceMemberError):
    pass


class WorkspaceMemberNotFoundError(WorkspaceMemberError):
    pass


class WorkspaceMemberOwnerError(WorkspaceMemberError):
    pass


class WorkspaceNameConflictError(ValueError):
    pass


def permissions_for_role(role: WorkspaceRole) -> list[str]:
    return ROLE_PERMISSIONS.get(role, VIEWER_PERMISSIONS).copy()


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
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_for_member(self, workspace_id: UUID, user_id: UUID) -> Workspace | None:
        statement = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(Workspace.id == workspace_id, WorkspaceMember.user_id == user_id)
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
            )
        )
        if exclude_workspace_id is not None:
            statement = statement.where(Workspace.id != exclude_workspace_id)
        return self.db.scalar(statement.limit(1)) is not None

    def list_members(self, *, workspace_id: UUID) -> list[WorkspaceMember]:
        statement = (
            select(WorkspaceMember)
            .options(joinedload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def add_member_by_email(
        self, *, workspace_id: UUID, email: str, role: WorkspaceRole = WorkspaceRole.member
    ) -> WorkspaceMember:
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
