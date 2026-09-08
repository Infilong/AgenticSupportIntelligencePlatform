"""Validate agent configuration references within the authorized workspace."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeDocument
from app.schemas.agent_configuration import AgentUpdateRequest


def agent_settings(db: Session, workspace_id: UUID, payload: AgentUpdateRequest) -> dict:
    settings = payload.model_dump(mode="json", exclude_none=True, include={
        "confidence_threshold", "retrieval_top_k", "retrieval_min_score", "instructions",
        "allowed_actions",
    })
    if "knowledge_document_ids" in payload.model_fields_set:
        requested = payload.knowledge_document_ids
        if requested is not None:
            ids = set(requested)
            found = set(db.scalars(select(KnowledgeDocument.id).where(
                KnowledgeDocument.workspace_id == workspace_id, KnowledgeDocument.id.in_(ids))))
            if found != ids:
                raise HTTPException(404, detail={"code": "knowledge_document_not_found",
                    "message": "One or more selected documents are not in this workspace."})
            settings["knowledge_document_ids"] = sorted(str(value) for value in ids)
        else:
            settings["knowledge_document_ids"] = None
    return settings
