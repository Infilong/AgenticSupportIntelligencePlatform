from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.knowledge import (
    DocumentChunkResponse,
    DocumentVersionResponse,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentIndexResponse,
    KnowledgeDocumentReindexRequest,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUploadRequest,
)
from app.services.knowledge_service import (
    KnowledgeDocumentIndexError,
    KnowledgeDocumentNotFoundError,
    KnowledgeService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["knowledge-documents"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
DocumentId = Annotated[UUID, Path()]


@router.post(
    "/knowledge-documents",
    response_model=KnowledgeDocumentIndexResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_knowledge_document(
    payload: KnowledgeDocumentUploadRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> KnowledgeDocumentIndexResponse:
    try:
        result = KnowledgeService(db).upload_document(
            workspace_id=workspace.id,
            title=payload.title,
            content_type=payload.content_type,
            content=payload.content,
            language=payload.language,
            current_user=current_user,
        )
    except KnowledgeDocumentIndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "knowledge_document_index_failed", "message": str(exc)},
        ) from exc
    return _index_response(result)


@router.get("/knowledge-documents", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> list[KnowledgeDocumentResponse]:
    documents = KnowledgeService(db).list_documents(workspace_id=workspace.id)
    return [KnowledgeDocumentResponse.model_validate(document) for document in documents]


@router.get(
    "/knowledge-documents/{document_id}", response_model=KnowledgeDocumentDetailResponse
)
def get_knowledge_document(
    document_id: DocumentId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> KnowledgeDocumentDetailResponse:
    try:
        detail = KnowledgeService(db).get_document_detail(
            workspace_id=workspace.id, document_id=document_id
        )
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "knowledge_document_not_found", "message": "Document was not found."},
        ) from exc
    return KnowledgeDocumentDetailResponse(
        document=KnowledgeDocumentResponse.model_validate(detail.document),
        latest_version=(
            DocumentVersionResponse.model_validate(detail.latest_version)
            if detail.latest_version is not None
            else None
        ),
        chunks=[DocumentChunkResponse.model_validate(chunk) for chunk in detail.chunks],
        embedding_count=detail.embedding_count,
    )


@router.post(
    "/knowledge-documents/{document_id}/reindex",
    response_model=KnowledgeDocumentIndexResponse,
)
def reindex_knowledge_document(
    document_id: DocumentId,
    payload: KnowledgeDocumentReindexRequest,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> KnowledgeDocumentIndexResponse:
    try:
        result = KnowledgeService(db).reindex_document(
            workspace_id=workspace.id,
            document_id=document_id,
            content_type=payload.content_type,
            content=payload.content,
            language=payload.language,
        )
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "knowledge_document_not_found", "message": "Document was not found."},
        ) from exc
    except KnowledgeDocumentIndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "knowledge_document_index_failed", "message": str(exc)},
        ) from exc
    return _index_response(result)


def _index_response(result) -> KnowledgeDocumentIndexResponse:
    return KnowledgeDocumentIndexResponse(
        document=KnowledgeDocumentResponse.model_validate(result.document),
        latest_version=DocumentVersionResponse.model_validate(result.latest_version),
        chunk_count=result.chunk_count,
        embedding_count=result.embedding_count,
    )
