"""Typed public run projections; internal checkpoint state is not an API contract."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.modules.knowledge.schemas import RetrievedPassage


class CitedPassage(RetrievedPassage):
    quote: str
    quote_start: int
    quote_end: int


class HandoffSummary(BaseModel):
    id: UUID
    context_hash: str
    provider: str
    prompt_version: str
    created_at: datetime
    submitted_at: datetime | None
    contributor_id: UUID | None
    handoff_elapsed_ms: float | None
    timing_status: Literal["pending", "recorded", "clock_anomaly"]


class StepSummary(BaseModel):
    id: UUID
    node: str
    status: str
    duration_ms: float | None
    job_attempt: int
    error_code: str | None


class CallSummary(BaseModel):
    id: UUID
    operation: str
    provider: str
    model: str
    revision: str
    status: str
    input_tokens: int | None
    duration_ms: float | None
    api_cost_usd: float | None
    error_code: str | None


class DevelopmentContext(BaseModel):
    original: str
    language: str
    instruction: str
    prompt_version: str
    sources: list[RetrievedPassage]


class HandoffExport(BaseModel):
    id: UUID
    context_hash: str
    provider: str
    prompt_version: str
    context: DevelopmentContext
