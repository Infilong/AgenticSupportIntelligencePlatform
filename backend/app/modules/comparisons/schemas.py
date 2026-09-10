"""Public comparison projections; no graph state or other generation requests are exposed."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.support.schemas import MessageInput


class ComparisonInput(MessageInput):
    generation_mode: Literal["manual", "local_ollama"] = "manual"


class ComparisonCreated(BaseModel):
    id: UUID


class ComparisonSummary(BaseModel):
    id: UUID
    question: str
    language: str
    cancelled: bool


class ComparisonList(BaseModel):
    items: list[ComparisonSummary]


class PipelineConfiguration(BaseModel):
    strategy: str | None
    limit: int
    context_bytes: int
    transport: str
    version: int
    model: str | None = Field(default=None, exclude_if=lambda value: value is None)


class PipelineResult(BaseModel):
    name: str
    configuration: PipelineConfiguration
    state: str
    outcome: str | None = None
    error_code: str | None
    job_id: UUID
    attempts: int
    retrieval_id: UUID | None
    run_id: UUID | None
    initial_response: dict[str, Any] | None
    response_hash: str | None
    request_hash: str | None
    contributor_id: UUID | None
    reviewed_response: str | None


class ComparisonDetail(ComparisonSummary):
    corpus_hash: str
    comparable: bool
    generation_quality: str
    pipelines: list[PipelineResult]
