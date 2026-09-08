from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.language import (
    LanguageDetectionError,
    SupportedLanguage,
    detect_language_for_messages,
)
from app.models.knowledge import (
    DocumentChunk,
    DocumentStatus,
    DocumentVersion,
    KnowledgeDocument,
)
from app.models.user import User
from app.services.document_parser import DocumentParseError, parse_text_document
from app.services.embedding_provider import EmbeddingProvider
from app.services.folder_service import ResourceFolderService
from app.services.knowledge_contracts import (
    KnowledgeDocumentDetail,
    KnowledgeDocumentIndexError,
    KnowledgeDocumentIndexResult,
    KnowledgeDocumentNotFoundError,
)
from app.services.knowledge_contracts import (
    KnowledgeDocumentError as KnowledgeDocumentError,
)
from app.services.knowledge_indexing import KnowledgeIndexer
from app.services.knowledge_mutation import commit_document_mutation


class KnowledgeService:
    def __init__(self, db: Session, embedding_provider: EmbeddingProvider | None = None):
        self.db = db
        self.embedding_provider = embedding_provider

    def upload_document(
        self,
        *,
        workspace_id: UUID,
        title: str,
        content_type: str,
        content: str,
        language: SupportedLanguage | None,
        current_user: User,
        folder_id: UUID | None = None,
    ) -> KnowledgeDocumentIndexResult:
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="knowledge_document"
        )
        raw_text = self._parse_or_raise(content=content, content_type=content_type)
        resolved_language = language or self._detect_or_raise(raw_text)
        document = KnowledgeDocument(
            workspace_id=workspace_id,
            title=title.strip(),
            language=resolved_language,
            status=DocumentStatus.pending,
            created_by_user_id=current_user.id,
            folder_id=folder_id,
        )
        self.db.add(document)
        self.db.flush()
        return KnowledgeIndexer(self.db, self.embedding_provider).index(
            document=document,
            workspace_id=workspace_id,
            content_type=content_type,
            raw_text=raw_text,
            language=resolved_language,
            version_number=1,
            actor_user_id=current_user.id, audit_action="uploaded",
        )

    def list_documents(
        self,
        *,
        workspace_id: UUID,
        folder_id: UUID | None = None,
        unfiled: bool = False,
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        conditions = self._document_filters(
            workspace_id=workspace_id, folder_id=folder_id, unfiled=unfiled, search=search
        )
        statement = (
            select(KnowledgeDocument)
            .where(*conditions)
            .order_by(KnowledgeDocument.created_at.desc())
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement).all())

    def count_documents(
        self,
        *,
        workspace_id: UUID,
        folder_id: UUID | None = None,
        unfiled: bool = False,
        search: str | None = None,
    ) -> int:
        conditions = self._document_filters(
            workspace_id=workspace_id, folder_id=folder_id, unfiled=unfiled, search=search
        )
        statement = select(func.count()).select_from(KnowledgeDocument).where(*conditions)
        return int(self.db.scalar(statement) or 0)

    def _document_filters(
        self,
        *,
        workspace_id: UUID,
        folder_id: UUID | None,
        unfiled: bool,
        search: str | None,
    ) -> list[object]:
        conditions = [KnowledgeDocument.workspace_id == workspace_id]
        if folder_id is not None:
            ResourceFolderService(self.db).validate_folder(
                workspace_id=workspace_id, folder_id=folder_id, resource_type="knowledge_document"
            )
            conditions.append(KnowledgeDocument.folder_id == folder_id)
        elif unfiled:
            conditions.append(KnowledgeDocument.folder_id.is_(None))
        normalized_search = (search or "").strip()
        if normalized_search:
            pattern = f"%{normalized_search}%"
            conditions.append(
                or_(
                    KnowledgeDocument.title.ilike(pattern),
                    cast(KnowledgeDocument.language, String).ilike(pattern),
                    cast(KnowledgeDocument.status, String).ilike(pattern),
                )
            )
        return conditions

    def get_document_detail(
        self, *, workspace_id: UUID, document_id: UUID
    ) -> KnowledgeDocumentDetail:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")
        latest_version = self.get_latest_version(workspace_id=workspace_id, document_id=document_id)
        chunks: list[DocumentChunk] = []
        embedding_count = 0
        if latest_version is not None:
            chunk_statement = (
                select(DocumentChunk)
                .options(selectinload(DocumentChunk.embedding))
                .where(
                    DocumentChunk.workspace_id == workspace_id,
                    DocumentChunk.document_version_id == latest_version.id,
                )
                .order_by(DocumentChunk.chunk_index.asc())
            )
            chunks = list(self.db.scalars(chunk_statement).all())
            embedding_count = sum(1 for chunk in chunks if chunk.embedding is not None)
        return KnowledgeDocumentDetail(
            document=document,
            latest_version=latest_version,
            chunks=chunks,
            embedding_count=embedding_count,
        )

    def reindex_document(
        self,
        *,
        workspace_id: UUID,
        document_id: UUID,
        title: str | None = None,
        content_type: str | None = None,
        content: str | None = None,
        language: SupportedLanguage | None = None,
        folder_id: UUID | None = None,
        update_folder: bool = False,
        actor_user_id: UUID | None = None,
    ) -> KnowledgeDocumentIndexResult:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id,
                                     for_update=True)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")

        latest_version = self.get_latest_version(workspace_id=workspace_id, document_id=document_id)
        if latest_version is None and content is None:
            raise KnowledgeDocumentIndexError("Cannot reindex without document content.")

        raw_text = self._parse_or_raise(
            content=content if content is not None else latest_version.raw_text,
            content_type=content_type if content_type is not None else latest_version.content_type,
        )
        if update_folder:
            ResourceFolderService(self.db).validate_folder(
                workspace_id=workspace_id, folder_id=folder_id, resource_type="knowledge_document"
            )
            document.folder_id = folder_id
        resolved_language = language or document.language or self._detect_or_raise(raw_text)
        if title is not None:
            document.title = title.strip()
        document.language = resolved_language
        next_version = self._next_version_number(workspace_id=workspace_id, document_id=document_id)
        return KnowledgeIndexer(self.db, self.embedding_provider).index(
            document=document,
            workspace_id=workspace_id,
            content_type=content_type if content_type is not None else latest_version.content_type,
            raw_text=raw_text,
            language=resolved_language,
            version_number=next_version,
            actor_user_id=actor_user_id, audit_action="reindexed",
        )

    def move_document(
        self, *, workspace_id: UUID, document_id: UUID, folder_id: UUID | None,
        actor_user_id: UUID,
    ) -> KnowledgeDocument:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id,
                                     for_update=True)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="knowledge_document"
        )
        document.folder_id = folder_id
        commit_document_mutation(self.db, document=document, actor_user_id=actor_user_id,
                                 action="moved")
        self.db.refresh(document)
        return document

    def delete_document(self, *, workspace_id: UUID, document_id: UUID,
                        actor_user_id: UUID) -> None:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id,
                                     for_update=True)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")
        self.db.delete(document)
        commit_document_mutation(self.db, document=document, actor_user_id=actor_user_id,
                                 action="deleted")

    def get_document(
        self, *, workspace_id: UUID, document_id: UUID, for_update: bool = False,
    ) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeDocument.id == document_id,
        )
        if for_update:
            statement = statement.with_for_update(key_share=True).execution_options(
                populate_existing=True,
            )
        return self.db.scalar(statement)

    def get_latest_version(
        self, *, workspace_id: UUID, document_id: UUID
    ) -> DocumentVersion | None:
        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.workspace_id == workspace_id,
                DocumentVersion.knowledge_document_id == document_id,
            )
            .order_by(DocumentVersion.version.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def _next_version_number(self, *, workspace_id: UUID, document_id: UUID) -> int:
        statement = select(func.max(DocumentVersion.version)).where(
            DocumentVersion.workspace_id == workspace_id,
            DocumentVersion.knowledge_document_id == document_id,
        )
        current_max = self.db.scalar(statement) or 0
        return int(current_max) + 1

    def _parse_or_raise(self, *, content: str, content_type: str) -> str:
        try:
            return parse_text_document(content=content, content_type=content_type)
        except DocumentParseError as exc:
            raise KnowledgeDocumentIndexError(str(exc)) from exc

    def _detect_or_raise(self, raw_text: str) -> SupportedLanguage:
        try:
            return detect_language_for_messages([raw_text[:2000]])
        except LanguageDetectionError as exc:
            raise KnowledgeDocumentIndexError(str(exc)) from exc
