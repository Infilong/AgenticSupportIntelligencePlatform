from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.reviews.schemas import DecisionSummary
from app.modules.support.projections import (
    AttemptSummary,
    CallSummary,
    CitedPassage,
    HandoffSummary,
    StepSummary,
)


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: str = Field(min_length=1, max_length=1000)
    language: Literal["en", "ja", "zh"]

    @field_validator("original")
    @classmethod
    def nonempty(cls, value):
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Enter valid Unicode text") from None
        if not value.strip() or "\x00" in value:
            raise ValueError("Enter a nonempty message without NUL characters")
        return value  # Preserve the exact original; normalization is a processing concern.


class CitationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: UUID
    quote: str = Field(min_length=1, max_length=2000)


class DevelopmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    context_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    request_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    answer: str = Field(min_length=1, max_length=8000)
    citations: list[CitationInput] = Field(min_length=1, max_length=5)
    review_category: Literal["ordinary", "policy_exception", "conflicting_evidence"] = "ordinary"

    @field_validator("answer", "context_hash")
    @classmethod
    def nonempty(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Enter nonempty text without NUL characters")
        return value


class MessageCreated(BaseModel):
    message_id: UUID
    run_id: UUID
    job_id: UUID


class MessageSummary(BaseModel):
    id: UUID
    original: str
    language: str
    created_at: datetime
    run_id: UUID | None
    labels: list[str]
    state: str
    outcome: str | None
    error_code: str | None


class MessagePage(BaseModel):
    items: list[MessageSummary]
    total: int


class RunDetail(BaseModel):
    id: UUID
    message_id: UUID
    parent_run_id: UUID | None
    creator_id: UUID
    attempt_number: int
    input_text: str
    clarification: str | None
    attempts: list[AttemptSummary]
    latest_run_id: UUID
    original: str
    language: str
    state: str
    outcome: str | None
    review_kind: str
    review_version: int
    draft_hash: str | None
    reviewed_response: str | None
    review: DecisionSummary | None
    job_id: UUID
    error_code: str | None
    draft: str | None
    citations: list[CitedPassage]
    handoff: HandoffSummary | None
    steps: list[StepSummary]
    model_calls: list[CallSummary]
    retrieval_id: UUID | None
    support_status: str = "not_verified"
