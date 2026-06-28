from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole


class WorkspaceService:
    def __init__(self, db: Session):
        self.db = db

    def create_workspace(self, *, name: str, creator: User) -> Workspace:
        workspace = Workspace(name=name.strip(), created_by_user_id=creator.id)
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
