from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.knowledge import (
    DocumentChunkResponse,
    DocumentVersionResponse,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentFolderUpdateRequest,
    KnowledgeDocumentIndexResponse,
    KnowledgeDocumentReindexRequest,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUploadRequest,
)
from app.services.audit_log_service import AuditLogService
from app.services.folder_service import ResourceFolderNotFoundError
from app.services.knowledge_service import (
    KnowledgeDocumentIndexError,
    KnowledgeDocumentNotFoundError,
    KnowledgeService,
)

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["knowledge-documents"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
KnowledgeReadAccess = Annotated[Workspace, Depends(require_workspace_permission("knowledge:read"))]
KnowledgeWriteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("knowledge:write"))
]
ResourceFolderManageAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resource_folders:manage"))
]
ResourceDeleteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resources:delete"))
]
FolderFilter = Annotated[UUID | None, Query()]
DocumentId = Annotated[UUID, Path()]


@router.post(
    "/knowledge-documents",
    response_model=KnowledgeDocumentIndexResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_knowledge_document(
    payload: KnowledgeDocumentUploadRequest,
    workspace: KnowledgeWriteAccess,
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
            folder_id=payload.folder_id,
        )
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    except KnowledgeDocumentIndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "knowledge_document_index_failed", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="knowledge_document.uploaded",
        resource_type="knowledge_document",
        resource_id=result.document.id,
        metadata={
            "title": result.document.title,
            "language": result.document.language,
            "chunk_count": result.chunk_count,
        },
    )
    return _index_response(result)


@router.get("/knowledge-documents", response_model=list[KnowledgeDocumentResponse])
def list_knowledge_documents(
    workspace: KnowledgeReadAccess,
    db: DbSession,
    folder_id: FolderFilter = None,
) -> list[KnowledgeDocumentResponse]:
    try:
        documents = KnowledgeService(db).list_documents(
            workspace_id=workspace.id, folder_id=folder_id
        )
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return [KnowledgeDocumentResponse.model_validate(document) for document in documents]


@router.get(
    "/knowledge-documents/{document_id}", response_model=KnowledgeDocumentDetailResponse
)
def get_knowledge_document(
    document_id: DocumentId,
    workspace: KnowledgeReadAccess,
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
    workspace: KnowledgeWriteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> KnowledgeDocumentIndexResponse:
    try:
        result = KnowledgeService(db).reindex_document(
            workspace_id=workspace.id,
            document_id=document_id,
            title=payload.title,
            content_type=payload.content_type,
            content=payload.content,
            language=payload.language,
            folder_id=payload.folder_id,
            update_folder="folder_id" in payload.model_fields_set,
        )
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "knowledge_document_not_found", "message": "Document was not found."},
        ) from exc
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    except KnowledgeDocumentIndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "knowledge_document_index_failed", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="knowledge_document.reindexed",
        resource_type="knowledge_document",
        resource_id=result.document.id,
        metadata={
            "title": result.document.title,
            "language": result.document.language,
            "version": result.latest_version.version,
            "chunk_count": result.chunk_count,
        },
    )
    return _index_response(result)


@router.patch("/knowledge-documents/{document_id}/folder", response_model=KnowledgeDocumentResponse)
def move_knowledge_document_folder(
    document_id: DocumentId,
    payload: KnowledgeDocumentFolderUpdateRequest,
    workspace: ResourceFolderManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> KnowledgeDocumentResponse:
    try:
        document = KnowledgeService(db).move_document(
            workspace_id=workspace.id, document_id=document_id, folder_id=payload.folder_id
        )
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "knowledge_document_not_found", "message": "Document was not found."},
        ) from exc
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="knowledge_document.moved",
        resource_type="knowledge_document",
        resource_id=document.id,
        metadata={"folder_id": str(document.folder_id) if document.folder_id else None},
    )
    return KnowledgeDocumentResponse.model_validate(document)


@router.delete("/knowledge-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(
    document_id: DocumentId,
    workspace: ResourceDeleteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        KnowledgeService(db).delete_document(workspace_id=workspace.id, document_id=document_id)
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "knowledge_document_not_found", "message": "Document was not found."},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="knowledge_document.deleted",
        resource_type="knowledge_document",
        resource_id=document_id,
    )


def _index_response(result) -> KnowledgeDocumentIndexResponse:
    return KnowledgeDocumentIndexResponse(
        document=KnowledgeDocumentResponse.model_validate(result.document),
        latest_version=DocumentVersionResponse.model_validate(result.latest_version),
        chunk_count=result.chunk_count,
        embedding_count=result.embedding_count,
    )


def _folder_not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "resource_folder_not_found", "message": "Resource folder was not found."},
    )
