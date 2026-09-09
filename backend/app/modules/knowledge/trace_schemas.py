"""Bounded candidate audit contract; scores are not confidence probabilities."""

from uuid import UUID

from pydantic import BaseModel, Field


class TraceCandidate(BaseModel):
    chunk_id: UUID
    document_id: UUID
    version_id: UUID
    title: str
    section: str
    start_offset: int
    currently_active: bool
    vector_rank: int | None = None
    cosine_similarity: float | None = None
    bm25_rank: int | None = None
    bm25_score: float | None = None
    fusion_rank: int | None = None
    fusion_score: float | None = None
    reranker_rank: int | None = None
    reranker_score: float | None = None
    final_rank: int | None = None
    selected_for_reranker: bool = False
    exclusion: str | None = None


class TraceDetail(BaseModel):
    id: UUID
    query: str
    status: str
    strategy: str
    duration_ms: float | None
    error_code: str | None
    trace_version: str | None
    phase: str
    candidate_queries_ms: float | None
    parameters: dict[str, float | str]
    candidates: list[TraceCandidate] = Field(max_length=40)
