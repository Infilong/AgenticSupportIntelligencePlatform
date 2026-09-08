from dataclasses import dataclass

from app.models.knowledge import DocumentChunk, DocumentVersion, KnowledgeDocument


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


