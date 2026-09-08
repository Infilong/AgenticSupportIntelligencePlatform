"""Commit dataset management with its audit in one database transaction."""

import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.dataset import Dataset


def commit_dataset_mutation(db: Session, *, dataset: Dataset,
                            actor_user_id: UUID, action: str) -> None:
    metadata = ({"name": dataset.name,
                 "folder_id": str(dataset.folder_id) if dataset.folder_id else None}
                if action == "moved" else {})
    try:
        db.flush()
        db.add(AuditLog(
            workspace_id=dataset.workspace_id, actor_user_id=actor_user_id,
            action=f"dataset.{action}", resource_type="dataset", resource_id=str(dataset.id),
            metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
