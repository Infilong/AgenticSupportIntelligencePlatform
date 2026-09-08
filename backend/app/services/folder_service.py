from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig
from app.models.audit import AuditLog
from app.models.dataset import Dataset
from app.models.evaluation import EvaluationRun
from app.models.folder import ResourceFolder
from app.models.knowledge import KnowledgeDocument
from app.models.user import User
from app.models.workspace import Workspace

VALID_RESOURCE_TYPES = {"knowledge_document", "dataset", "evaluation_run", "agent_config"}


@dataclass(frozen=True)
class ResourceFolderCountSummary:
    resource_type: str
    total_count: int
    unfiled_count: int
    folder_counts: dict[UUID, int]


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

    def count_resources(
        self, *, workspace_id: UUID, resource_type: str
    ) -> ResourceFolderCountSummary:
        model = self._model_for_resource_type(resource_type)
        total_count = int(
            self.db.scalar(
                select(func.count(model.id)).where(model.workspace_id == workspace_id)
            )
            or 0
        )
        unfiled_count = int(
            self.db.scalar(
                select(func.count(model.id)).where(
                    model.workspace_id == workspace_id,
                    model.folder_id.is_(None),
                )
            )
            or 0
        )
        rows = self.db.execute(
            select(model.folder_id, func.count(model.id))
            .where(model.workspace_id == workspace_id, model.folder_id.is_not(None))
            .group_by(model.folder_id)
        ).all()
        return ResourceFolderCountSummary(
            resource_type=resource_type,
            total_count=total_count,
            unfiled_count=unfiled_count,
            folder_counts={
                folder_id: int(count) for folder_id, count in rows if folder_id is not None
            },
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
        self._commit_mutation(folder, current_user.id, "created")
        self.db.refresh(folder)
        return folder

    def update_folder(
        self,
        *,
        workspace_id: UUID,
        folder_id: UUID,
        name: str | None,
        parent_folder_id: UUID | None,
        actor_user_id: UUID,
        update_parent: bool = True,
    ) -> ResourceFolder:
        if update_parent:
            # Serialize parent changes without conflicting with FK key-share locks.
            self.db.execute(select(Workspace.id).where(Workspace.id == workspace_id)
                            .with_for_update(key_share=True))
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
            if update_parent:
                self._validate_ancestry(folder, parent_folder_id)
        if name is not None:
            folder.name = name.strip()
        if update_parent:
            folder.parent_folder_id = parent_folder_id
        self._commit_mutation(folder, actor_user_id, "updated")
        self.db.refresh(folder)
        return folder

    def _validate_ancestry(self, folder: ResourceFolder, parent_id: UUID) -> None:
        visited = {folder.id}
        current: UUID | None = parent_id
        while current is not None:
            if current in visited:
                raise ResourceFolderInvalidTypeError("Folder movement would create a cycle.")
            visited.add(current)
            # Column reads bypass stale ORM instances after a competing move commits.
            row = self.db.execute(select(ResourceFolder.parent_folder_id).where(
                ResourceFolder.id == current, ResourceFolder.workspace_id == folder.workspace_id,
                ResourceFolder.resource_type == folder.resource_type,
            )).first()
            if row is None:
                raise ResourceFolderNotFoundError("Resource folder was not found.")
            current = row[0]

    def delete_folder(self, *, workspace_id: UUID, folder_id: UUID, actor_user_id: UUID) -> None:
        folder = self.get_folder(workspace_id=workspace_id, folder_id=folder_id)
        if folder is None:
            raise ResourceFolderNotFoundError("Resource folder was not found.")
        if self._has_children(workspace_id=workspace_id, folder_id=folder.id):
            raise ResourceFolderNotEmptyError("Folder has child folders.")
        if self._has_assigned_resources(workspace_id=workspace_id, folder=folder):
            raise ResourceFolderNotEmptyError("Folder contains resources.")
        self.db.delete(folder)
        self._commit_mutation(folder, actor_user_id, "deleted")

    def _commit_mutation(self, folder: ResourceFolder, actor: UUID, action: str) -> None:
        try:
            self.db.flush()
            metadata = {} if action == "deleted" else {
                "name": folder.name, "resource_type": folder.resource_type,
            }
            self.db.add(AuditLog(
                workspace_id=folder.workspace_id, actor_user_id=actor,
                action=f"resource_folder.{action}", resource_type="resource_folder",
                resource_id=str(folder.id),
                metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            ))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_folder(self, *, workspace_id: UUID, folder_id: UUID) -> ResourceFolder | None:
        return self.db.scalar(
            select(ResourceFolder).where(
                ResourceFolder.workspace_id == workspace_id,
                ResourceFolder.id == folder_id,
            ).execution_options(populate_existing=True)
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

    def _model_for_resource_type(self, resource_type: str):
        self._validate_resource_type(resource_type)
        if resource_type == "knowledge_document":
            return KnowledgeDocument
        if resource_type == "dataset":
            return Dataset
        if resource_type == "evaluation_run":
            return EvaluationRun
        if resource_type == "agent_config":
            return AgentConfig
        self._validate_resource_type(resource_type)
        raise ResourceFolderInvalidTypeError("Unsupported resource folder type.")

    def _validate_resource_type(self, resource_type: str) -> None:
        if resource_type not in VALID_RESOURCE_TYPES:
            raise ResourceFolderInvalidTypeError("Unsupported resource folder type.")
