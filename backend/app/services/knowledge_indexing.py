import hashlib
import json
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.knowledge import (
    DocumentChunk,
    DocumentStatus,
    DocumentVersion,
    Embedding,
    KnowledgeDocument,
)
from app.services.chunking import chunk_text
from app.services.embedding_provider import EmbeddingProvider
from app.services.embedding_runtime import configured_embedding_provider
from app.services.knowledge_contracts import (
    KnowledgeDocumentIndexError,
    KnowledgeDocumentIndexResult,
)
from app.services.knowledge_mutation import commit_document_mutation


class KnowledgeIndexer:
    def __init__(self, db: Session, provider: EmbeddingProvider | None = None):
        self.db = db
        self.provider = provider

    def index(
        self,
        *,
        document: KnowledgeDocument,
        workspace_id: UUID,
        content_type: str,
        raw_text: str,
        language: SupportedLanguage,
        version_number: int,
        actor_user_id: UUID | None,
        audit_action: str,
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
            provider = self.provider or configured_embedding_provider(
                self.db, workspace_id=workspace_id, language=language, purpose="embedding_document")
            text_chunks = chunk_text(raw_text, language)
            if not text_chunks:
                raise KnowledgeDocumentIndexError("Document did not produce any chunks.")
            vectors = provider.embed_texts([chunk.content for chunk in text_chunks])
            if len(vectors) != len(text_chunks):
                raise KnowledgeDocumentIndexError(
                    "Embedding provider returned an invalid vector count."
                )
            for text_chunk, vector in zip(text_chunks, vectors, strict=True):
                if len(vector) != provider.dimensions:
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
                        provider=provider.provider,
                        model=provider.model,
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
        metadata = {"title": document.title, "language": document.language,
                    "chunk_count": len(text_chunks)}
        if audit_action == "reindexed":
            metadata["version"] = version_number
        commit_document_mutation(self.db, document=document, actor_user_id=actor_user_id,
                                 action=audit_action, metadata=metadata)
        self.db.refresh(document)
        self.db.refresh(version)
        return KnowledgeDocumentIndexResult(
            document=document,
            latest_version=version,
            chunk_count=len(text_chunks),
            embedding_count=len(vectors),
        )

