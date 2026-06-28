from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun
from app.models.folder import ResourceFolder
from app.models.knowledge import KnowledgeDocument
from app.models.user import User

VALID_RESOURCE_TYPES = {"knowledge_document", "dataset", "evaluation_run", "agent_config"}


class ResourceFolderError(ValueError):
    pass


class ResourceFolderNotFoundError(ResourceFolderError):
    pass


class ResourceFolderNotEmptyError(ResourceFolderError):
    pass


class ResourceFolderInvalidTypeError(ResourceFolderError):
    pass


class ResourceFolderService:
    def __init__(self, db: Session):
        self.db = db

    def list_folders(self, *, workspace_id: UUID, resource_type: str) -> list[ResourceFolder]:
        self._validate_resource_type(resource_type)
        return list(
            self.db.scalars(
                select(ResourceFolder)
                .where(
                    ResourceFolder.workspace_id == workspace_id,
                    ResourceFolder.resource_type == resource_type,
                )
                .order_by(ResourceFolder.name.asc(), ResourceFolder.created_at.asc())
            ).all()
        )

    def create_folder(
        self,
        *,
        workspace_id: UUID,
        resource_type: str,
        name: str,
        parent_folder_id: UUID | None,
        current_user: User,
    ) -> ResourceFolder:
        self._validate_resource_type(resource_type)
        if parent_folder_id is not None:
            self.validate_folder(
                workspace_id=workspace_id,
                folder_id=parent_folder_id,
                resource_type=resource_type,
            )
        folder = ResourceFolder(
            workspace_id=workspace_id,
            resource_type=resource_type,
            name=name.strip(),
            parent_folder_id=parent_folder_id,
            created_by_user_id=current_user.id,
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def update_folder(
        self,
        *,
        workspace_id: UUID,
        folder_id: UUID,
        name: str | None,
        parent_folder_id: UUID | None,
    ) -> ResourceFolder:
        folder = self.get_folder(workspace_id=workspace_id, folder_id=folder_id)
        if folder is None:
            raise ResourceFolderNotFoundError("Resource folder was not found.")
        if parent_folder_id == folder.id:
            raise ResourceFolderInvalidTypeError("A folder cannot be its own parent.")
        if parent_folder_id is not None:
            self.validate_folder(
                workspace_id=workspace_id,
                folder_id=parent_folder_id,
                resource_type=folder.resource_type,
            )
        if name is not None:
            folder.name = name.strip()
        folder.parent_folder_id = parent_folder_id
        self.db.commit()
        self.db.refresh(folder)
        return folder

    def delete_folder(self, *, workspace_id: UUID, folder_id: UUID) -> None:
        folder = self.get_folder(workspace_id=workspace_id, folder_id=folder_id)
        if folder is None:
            raise ResourceFolderNotFoundError("Resource folder was not found.")
        if self._has_children(workspace_id=workspace_id, folder_id=folder.id):
            raise ResourceFolderNotEmptyError("Folder has child folders.")
        if self._has_assigned_resources(workspace_id=workspace_id, folder=folder):
            raise ResourceFolderNotEmptyError("Folder contains resources.")
        self.db.delete(folder)
        self.db.commit()

    def get_folder(self, *, workspace_id: UUID, folder_id: UUID) -> ResourceFolder | None:
        return self.db.scalar(
            select(ResourceFolder).where(
                ResourceFolder.workspace_id == workspace_id,
                ResourceFolder.id == folder_id,
            )
        )

    def validate_folder(
        self, *, workspace_id: UUID, folder_id: UUID | None, resource_type: str
    ) -> ResourceFolder | None:
        if folder_id is None:
            return None
        self._validate_resource_type(resource_type)
        folder = self.db.scalar(
            select(ResourceFolder).where(
                ResourceFolder.workspace_id == workspace_id,
                ResourceFolder.id == folder_id,
                ResourceFolder.resource_type == resource_type,
            )
        )
        if folder is None:
            raise ResourceFolderNotFoundError("Resource folder was not found.")
        return folder

    def _has_children(self, *, workspace_id: UUID, folder_id: UUID) -> bool:
        return (
            self.db.scalar(
                select(ResourceFolder.id)
                .where(
                    ResourceFolder.workspace_id == workspace_id,
                    ResourceFolder.parent_folder_id == folder_id,
                )
                .limit(1)
            )
            is not None
        )

    def _has_assigned_resources(self, *, workspace_id: UUID, folder: ResourceFolder) -> bool:
        if folder.resource_type == "knowledge_document":
            statement = select(KnowledgeDocument.id).where(
                KnowledgeDocument.workspace_id == workspace_id,
                KnowledgeDocument.folder_id == folder.id,
            )
        elif folder.resource_type == "dataset":
            statement = select(Dataset.id).where(
                Dataset.workspace_id == workspace_id,
                Dataset.folder_id == folder.id,
            )
        elif folder.resource_type == "evaluation_run":
            statement = select(EvaluationRun.id).where(
                EvaluationRun.workspace_id == workspace_id,
                EvaluationRun.folder_id == folder.id,
            )
        elif folder.resource_type == "agent_config":
            statement = select(AgentConfig.id).where(
                AgentConfig.workspace_id == workspace_id,
                AgentConfig.folder_id == folder.id,
            )
        else:
            self._validate_resource_type(folder.resource_type)
            return False
        return self.db.scalar(statement.limit(1)) is not None

    def _validate_resource_type(self, resource_type: str) -> None:
        if resource_type not in VALID_RESOURCE_TYPES:
            raise ResourceFolderInvalidTypeError("Unsupported resource folder type.")
