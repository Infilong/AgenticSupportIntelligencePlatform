from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.language import (
    LanguageDetectionError,
    SupportedLanguage,
    detect_language_for_messages,
)
from app.models.knowledge import (
    DocumentChunk,
    DocumentVersion,
    Embedding,
    KnowledgeDocument,
)
from app.models.retrieval import RetrievalTrace, RetrievedChunk
from app.services.embedding_provider import EmbeddingProvider, MockEmbeddingProvider
from app.services.embedding_runtime import configured_embedding_provider
from app.services.lexical_search import lexical_score
from app.services.retrieval_candidates import candidate_statement, postgres_candidates
from app.services.retrieval_embeddings import RetrievalError, embed_query


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
    database_score: float | None = None


class RetrievalService:
    def __init__(self, db: Session, embedding_provider: EmbeddingProvider | None = None,
                 *, strategy: str = "hybrid", allowed_document_ids: list[UUID] | None = None):
        if strategy not in {"hybrid", "vector", "lexical"}:
            raise ValueError("Unsupported retrieval strategy")
        self.strategy = strategy
        self.allowed_document_ids = allowed_document_ids
        self.db = db
        self.embedding_provider = embedding_provider or MockEmbeddingProvider()
        self.configured = (embedding_provider is None
                           and get_settings().embedding_provider == "openai")
        if (strategy == "hybrid" and self.embedding_provider.provider == "mock"
                and not self.configured):
            self.strategy = "lexical"

    def search(
        self,
        *,
        workspace_id: UUID,
        query: str,
        language: SupportedLanguage | None,
        top_k: int,
        min_score: float,
        document_id: UUID | None,
        graph_run_id: UUID | None = None,
    ) -> RetrievalSearchResult:
        started = time.perf_counter()
        resolved_language = language or self._detect_language(query)
        if self.configured:
            self.embedding_provider = configured_embedding_provider(
                self.db, workspace_id=workspace_id,
                language=resolved_language, purpose="embedding_query", graph_run_id=graph_run_id)
        filters = {
            "language": resolved_language.value,
            "document_id": str(document_id) if document_id else None,
        }
        if self.allowed_document_ids is not None:
            filters["allowed_document_ids"] = [str(value) for value in self.allowed_document_ids]
        trace = RetrievalTrace(
            workspace_id=workspace_id,
            graph_run_id=graph_run_id,
            query=query,
            language=resolved_language,
            strategy=self.strategy,
            filters_json=json.dumps(filters, sort_keys=True),
            latency_ms=0,
            no_source=False,
            outcome="pending",
        )
        self.db.add(trace)
        self.db.flush()

        query_vector = []
        postgres = self.db.get_bind().dialect.name == "postgresql" and self.strategy != "lexical"
        if postgres:
            try:
                statement = candidate_statement(
                    workspace_id=workspace_id, language=resolved_language,
                    document_id=document_id, allowed_document_ids=self.allowed_document_ids,
                    strategy=self.strategy, provider=self.embedding_provider)
                rows, query_vector = postgres_candidates(
                    self.db, statement, self.embedding_provider, query,
                    top_k if self.strategy == "vector" else max(100, top_k * 10))
                candidates = [RetrievalCandidate(chunk, embedding, version, document,
                    max(0.0, min(1.0, 1.0 - distance / 2.0)))
                    for chunk, embedding, version, document, distance in rows]
            except (RuntimeError, ValueError) as exc:
                trace.no_source = True
                trace.outcome = "failed"
                trace.error_code = "embedding_failed"
                trace.latency_ms = max(1, int((time.perf_counter() - started) * 1000))
                raise RetrievalError(str(exc), trace_id=trace.id) from exc
        else:
            candidates = self._load_candidates(workspace_id=workspace_id,
                language=resolved_language, document_id=document_id)
        if not candidates:
            trace.no_source = True
            trace.outcome = "succeeded"
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

        if self.strategy != "lexical" and not postgres:
            try:
                query_vector = embed_query(self.embedding_provider, query,
                    [candidate.embedding.vector for candidate in candidates])
            except (RuntimeError, ValueError) as exc:
                trace.no_source = True
                trace.outcome = "failed"
                trace.error_code = "embedding_failed"
                trace.latency_ms = max(1, int((time.perf_counter() - started) * 1000))
                raise RetrievalError(str(exc), trace_id=trace.id) from exc
        scored = [
            self._score_candidate(query, query_vector, resolved_language, candidate)
            for candidate in candidates
        ]
        scored = [result for result in scored if result.combined_score >= min_score]
        scored.sort(key=lambda result: result.combined_score, reverse=True)
        limited = scored[:top_k]

        trace.no_source = not limited
        trace.outcome = "succeeded"
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
        statement = candidate_statement(workspace_id=workspace_id, language=language,
            document_id=document_id, allowed_document_ids=self.allowed_document_ids,
            strategy=self.strategy, provider=self.embedding_provider)
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
        vector_score = (None if self.strategy == "lexical" else
                        candidate.database_score if candidate.database_score is not None else
                        _cosine_similarity(query_vector, candidate.embedding.vector))
        lex_score = (lexical_score(query, candidate.chunk.content, language)
                     if self.strategy != "vector" else 0.0)
        if self.strategy == "lexical":
            combined_score = round(lex_score, 6)
        elif self.strategy == "vector":
            combined_score = round(vector_score, 6)
        else:
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
            vector_score=round(vector_score, 6) if vector_score is not None else None,
            lexical_score=round(lex_score, 6) if self.strategy != "vector" else None,
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
