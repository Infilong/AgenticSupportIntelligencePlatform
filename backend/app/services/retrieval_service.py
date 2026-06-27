from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

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
from app.models.retrieval import RetrievalTrace, RetrievedChunk
from app.services.embedding_provider import EmbeddingProvider, MockEmbeddingProvider
from app.services.lexical_search import lexical_score


class RetrievalError(ValueError):
    pass


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    version: int
    chunk_index: int
    language: SupportedLanguage
    content: str
    token_count: int
    vector_score: float | None
    lexical_score: float | None
    combined_score: float
    citation: str


@dataclass(frozen=True)
class RetrievalSearchResult:
    trace_id: UUID
    language: SupportedLanguage
    strategy: str
    no_source: bool
    results: list[RetrievalResult]


@dataclass(frozen=True)
class RetrievalCandidate:
    chunk: DocumentChunk
    embedding: Embedding
    version: DocumentVersion
    document: KnowledgeDocument


class RetrievalService:
    strategy = "hybrid"

    def __init__(self, db: Session, embedding_provider: EmbeddingProvider | None = None):
        self.db = db
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()

    def search(
        self,
        *,
        workspace_id: UUID,
        query: str,
        language: SupportedLanguage | None,
        top_k: int,
        min_score: float,
        document_id: UUID | None,
    ) -> RetrievalSearchResult:
        started = time.perf_counter()
        resolved_language = language or self._detect_language(query)
        filters = {
            "language": resolved_language.value,
            "document_id": str(document_id) if document_id else None,
        }
        trace = RetrievalTrace(
            workspace_id=workspace_id,
            graph_run_id=None,
            query=query,
            language=resolved_language,
            strategy=self.strategy,
            filters_json=json.dumps(filters, sort_keys=True),
            latency_ms=0,
            no_source=False,
        )
        self.db.add(trace)
        self.db.flush()

        candidates = self._load_candidates(
            workspace_id=workspace_id,
            language=resolved_language,
            document_id=document_id,
        )
        if not candidates:
            trace.no_source = True
            trace.latency_ms = max(1, int((time.perf_counter() - started) * 1000))
            self.db.commit()
            self.db.refresh(trace)
            return RetrievalSearchResult(
                trace_id=trace.id,
                language=resolved_language,
                strategy=self.strategy,
                no_source=True,
                results=[],
            )

        query_vector = self.embedding_provider.embed_texts([query])[0]
        scored = [
            self._score_candidate(query, query_vector, resolved_language, candidate)
            for candidate in candidates
        ]
        scored = [result for result in scored if result.combined_score >= min_score]
        scored.sort(key=lambda result: result.combined_score, reverse=True)
        limited = scored[:top_k]

        trace.no_source = not limited
        trace.latency_ms = max(1, int((time.perf_counter() - started) * 1000))
        for rank, result in enumerate(limited, start=1):
            self.db.add(
                RetrievedChunk(
                    workspace_id=workspace_id,
                    retrieval_trace_id=trace.id,
                    document_chunk_id=result.chunk_id,
                    rank=rank,
                    vector_score=result.vector_score,
                    lexical_score=result.lexical_score,
                    combined_score=result.combined_score,
                    citation=result.citation,
                )
            )
        self.db.commit()
        self.db.refresh(trace)
        return RetrievalSearchResult(
            trace_id=trace.id,
            language=resolved_language,
            strategy=self.strategy,
            no_source=trace.no_source,
            results=limited,
        )

    def _load_candidates(
        self,
        *,
        workspace_id: UUID,
        language: SupportedLanguage,
        document_id: UUID | None,
    ) -> list[RetrievalCandidate]:
        statement = (
            select(DocumentChunk, Embedding, DocumentVersion, KnowledgeDocument)
            .join(Embedding, Embedding.document_chunk_id == DocumentChunk.id)
            .join(DocumentVersion, DocumentVersion.id == DocumentChunk.document_version_id)
            .join(KnowledgeDocument, KnowledgeDocument.id == DocumentVersion.knowledge_document_id)
            .where(
                DocumentChunk.workspace_id == workspace_id,
                Embedding.workspace_id == workspace_id,
                DocumentVersion.workspace_id == workspace_id,
                KnowledgeDocument.workspace_id == workspace_id,
                KnowledgeDocument.status == DocumentStatus.indexed,
                DocumentChunk.language == language,
            )
        )
        if document_id is not None:
            statement = statement.where(KnowledgeDocument.id == document_id)
        rows = self.db.execute(statement).all()
        return [
            RetrievalCandidate(chunk=chunk, embedding=embedding, version=version, document=document)
            for chunk, embedding, version, document in rows
        ]

    def _score_candidate(
        self,
        query: str,
        query_vector: list[float],
        language: SupportedLanguage,
        candidate: RetrievalCandidate,
    ) -> RetrievalResult:
        vector_score = _cosine_similarity(query_vector, candidate.embedding.vector)
        lex_score = lexical_score(query, candidate.chunk.content, language)
        combined_score = round((0.35 * vector_score) + (0.65 * lex_score), 6)
        citation = _citation(candidate.document, candidate.version, candidate.chunk)
        return RetrievalResult(
            chunk_id=candidate.chunk.id,
            document_id=candidate.document.id,
            document_title=candidate.document.title,
            version=candidate.version.version,
            chunk_index=candidate.chunk.chunk_index,
            language=language,
            content=candidate.chunk.content,
            token_count=candidate.chunk.token_count,
            vector_score=round(vector_score, 6),
            lexical_score=round(lex_score, 6),
            combined_score=combined_score,
            citation=citation,
        )

    def _detect_language(self, query: str) -> SupportedLanguage:
        try:
            return detect_language_for_messages([query])
        except LanguageDetectionError as exc:
            raise RetrievalError(str(exc)) from exc


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    cosine = dot / (left_norm * right_norm)
    return max(0.0, min(1.0, (cosine + 1.0) / 2.0))


def _citation(document: KnowledgeDocument, version: DocumentVersion, chunk: DocumentChunk) -> str:
    return f"{document.title} v{version.version} #chunk-{chunk.chunk_index} ({chunk.id})"
