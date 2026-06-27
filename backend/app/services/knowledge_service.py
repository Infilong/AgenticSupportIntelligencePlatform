from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
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
    Embedding,
    KnowledgeDocument,
)
from app.models.user import User
from app.services.chunking import chunk_text
from app.services.document_parser import DocumentParseError, parse_text_document
from app.services.embedding_provider import EmbeddingProvider, MockEmbeddingProvider


class KnowledgeDocumentError(ValueError):
    pass


class KnowledgeDocumentNotFoundError(KnowledgeDocumentError):
    pass


class KnowledgeDocumentIndexError(KnowledgeDocumentError):
    pass


@dataclass(frozen=True)
class KnowledgeDocumentIndexResult:
    document: KnowledgeDocument
    latest_version: DocumentVersion
    chunk_count: int
    embedding_count: int


@dataclass(frozen=True)
class KnowledgeDocumentDetail:
    document: KnowledgeDocument
    latest_version: DocumentVersion | None
    chunks: list[DocumentChunk]
    embedding_count: int


class KnowledgeService:
    def __init__(self, db: Session, embedding_provider: EmbeddingProvider | None = None):
        self.db = db
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()

    def upload_document(
        self,
        *,
        workspace_id: UUID,
        title: str,
        content_type: str,
        content: str,
        language: SupportedLanguage | None,
        current_user: User,
    ) -> KnowledgeDocumentIndexResult:
        raw_text = self._parse_or_raise(content=content, content_type=content_type)
        resolved_language = language or self._detect_or_raise(raw_text)
        document = KnowledgeDocument(
            workspace_id=workspace_id,
            title=title.strip(),
            language=resolved_language,
            status=DocumentStatus.pending,
            created_by_user_id=current_user.id,
        )
        self.db.add(document)
        self.db.flush()
        return self._index_document_version(
            document=document,
            workspace_id=workspace_id,
            content_type=content_type,
            raw_text=raw_text,
            language=resolved_language,
            version_number=1,
        )

    def list_documents(self, *, workspace_id: UUID) -> list[KnowledgeDocument]:
        statement = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.workspace_id == workspace_id)
            .order_by(KnowledgeDocument.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

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
    ) -> KnowledgeDocumentIndexResult:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")

        latest_version = self.get_latest_version(workspace_id=workspace_id, document_id=document_id)
        if latest_version is None and content is None:
            raise KnowledgeDocumentIndexError("Cannot reindex without document content.")

        raw_text = self._parse_or_raise(
            content=content if content is not None else latest_version.raw_text,
            content_type=content_type if content_type is not None else latest_version.content_type,
        )
        resolved_language = language or document.language or self._detect_or_raise(raw_text)
        if title is not None:
            document.title = title.strip()
        document.language = resolved_language
        next_version = self._next_version_number(workspace_id=workspace_id, document_id=document_id)
        return self._index_document_version(
            document=document,
            workspace_id=workspace_id,
            content_type=content_type if content_type is not None else latest_version.content_type,
            raw_text=raw_text,
            language=resolved_language,
            version_number=next_version,
        )

    def delete_document(self, *, workspace_id: UUID, document_id: UUID) -> None:
        document = self.get_document(workspace_id=workspace_id, document_id=document_id)
        if document is None:
            raise KnowledgeDocumentNotFoundError("Knowledge document was not found.")
        self.db.delete(document)
        self.db.commit()

    def get_document(
        self, *, workspace_id: UUID, document_id: UUID
    ) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeDocument.id == document_id,
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

    def _index_document_version(
        self,
        *,
        document: KnowledgeDocument,
        workspace_id: UUID,
        content_type: str,
        raw_text: str,
        language: SupportedLanguage,
        version_number: int,
    ) -> KnowledgeDocumentIndexResult:
        document.status = DocumentStatus.indexing
        document.error_message = None
        version = DocumentVersion(
            workspace_id=workspace_id,
            knowledge_document_id=document.id,
            version=version_number,
            content_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            content_type=content_type.strip().lower(),
            raw_text=raw_text,
        )
        self.db.add(version)
        self.db.flush()

        try:
            text_chunks = chunk_text(raw_text, language)
            if not text_chunks:
                raise KnowledgeDocumentIndexError("Document did not produce any chunks.")
            vectors = self.embedding_provider.embed_texts([chunk.content for chunk in text_chunks])
            if len(vectors) != len(text_chunks):
                raise KnowledgeDocumentIndexError(
                    "Embedding provider returned an invalid vector count."
                )
            for text_chunk, vector in zip(text_chunks, vectors, strict=True):
                if len(vector) != self.embedding_provider.dimensions:
                    raise KnowledgeDocumentIndexError(
                        "Embedding provider returned an invalid dimension."
                    )
                chunk = DocumentChunk(
                    workspace_id=workspace_id,
                    document_version_id=version.id,
                    language=language,
                    chunk_index=text_chunk.chunk_index,
                    content=text_chunk.content,
                    token_count=text_chunk.token_count,
                    chunk_metadata=json.dumps(text_chunk.metadata, sort_keys=True),
                )
                self.db.add(chunk)
                self.db.flush()
                self.db.add(
                    Embedding(
                        workspace_id=workspace_id,
                        document_chunk_id=chunk.id,
                        provider=self.embedding_provider.provider,
                        model=self.embedding_provider.model,
                        vector=vector,
                    )
                )
        except (KnowledgeDocumentIndexError, RuntimeError, ValueError) as exc:
            document.status = DocumentStatus.failed
            document.error_message = str(exc)
            self.db.commit()
            self.db.refresh(document)
            raise KnowledgeDocumentIndexError(str(exc)) from exc

        document.status = DocumentStatus.indexed
        document.error_message = None
        self.db.commit()
        self.db.refresh(document)
        self.db.refresh(version)
        return KnowledgeDocumentIndexResult(
            document=document,
            latest_version=version,
            chunk_count=len(text_chunks),
            embedding_count=len(vectors),
        )

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
