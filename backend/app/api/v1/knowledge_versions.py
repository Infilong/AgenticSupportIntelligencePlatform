from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_permission
from app.models.knowledge import DocumentVersion, KnowledgeDocument
from app.models.workspace import Workspace
from app.schemas.knowledge import DocumentVersionResponse

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["knowledge-documents"])


@router.get("/knowledge-documents/{document_id}/versions/{version}",
            response_model=DocumentVersionResponse)
def read_version(
    document_id: UUID,
    version: Annotated[int, Path(ge=1)],
    workspace: Annotated[Workspace, Depends(require_workspace_permission("knowledge:read"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentVersionResponse:
    saved = db.scalar(select(DocumentVersion).join(
        KnowledgeDocument, KnowledgeDocument.id == DocumentVersion.knowledge_document_id,
    ).where(
        KnowledgeDocument.workspace_id == workspace.id,
        KnowledgeDocument.id == document_id,
        DocumentVersion.workspace_id == workspace.id,
        DocumentVersion.version == version,
    ))
    if saved is None:
        raise HTTPException(status_code=404, detail="Document version was not found.")
    return DocumentVersionResponse.model_validate(saved)
