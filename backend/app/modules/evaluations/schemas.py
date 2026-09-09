"""Allowlisted historical evidence, never a raw evaluation artifact."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StrategyName = Literal["vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank"]


class EvaluationCase(BaseModel):
    id: str
    language: Literal["en", "ja", "zh"]
    question: str
    trace_id: UUID
    passed: bool | None
    groups_found: int
    total_groups: int
    elapsed_seconds: float


class EvaluationScore(BaseModel):
    passed: int
    total: int
    groups_found: int
    total_groups: int


class EvaluationStrategy(BaseModel):
    name: StrategyName
    scores: dict[str, EvaluationScore]
    warm_p95_seconds: float
    measured_requests: int
    safety_passed: bool
    retrieval_gate_passed: bool
    cases: list[EvaluationCase]


class EvaluationSnapshot(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    scorer_version: str
    source_commit: str
    source_sha256: str
    corpus_sha256: str
    generation: Literal["not_verified"] = "not_verified"
    strategies: list[EvaluationStrategy]


class EvaluationSummary(BaseModel):
    id: UUID
    registered_at: datetime
    report_sha256: str
    source_commit: str


class EvaluationDetail(EvaluationSummary):
    snapshot: EvaluationSnapshot


class EvaluationList(BaseModel):
    items: list[EvaluationSummary] = Field(max_length=20)
    more: bool
