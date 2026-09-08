"""Commit document management and its attributable audit as one transaction."""

import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.knowledge import KnowledgeDocument


def commit_document_mutation(db: Session, *, document: KnowledgeDocument,
                             actor_user_id: UUID | None, action: str,
                             metadata: dict | None = None) -> None:
    if metadata is None:
        metadata = ({"folder_id": str(document.folder_id) if document.folder_id else None}
                    if action == "moved" else {})
    try:
        db.flush()
        db.add(AuditLog(
            workspace_id=document.workspace_id, actor_user_id=actor_user_id,
            action=f"knowledge_document.{action}", resource_type="knowledge_document",
            resource_id=str(document.id), metadata_json=json.dumps(metadata, sort_keys=True),
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
