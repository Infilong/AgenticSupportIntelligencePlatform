from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: str = Field(min_length=1, max_length=1000)
    language: Literal["en", "ja", "zh"]

    @field_validator("original")
    @classmethod
    def nonempty(cls, value):
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
    answer: str = Field(min_length=1, max_length=8000)
    citations: list[CitationInput] = Field(min_length=1, max_length=5)

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
    run_id: UUID
    state: str
    error_code: str | None


class MessagePage(BaseModel):
    items: list[MessageSummary]
    total: int


class RunDetail(BaseModel):
    id: UUID
    message_id: UUID
    original: str
    language: str
    state: str
    job_id: UUID
    error_code: str | None
    draft: str | None
    citations: list[dict]
    handoff: dict | None
    steps: list[dict]
    model_calls: list[dict]
    retrieval_id: UUID | None
    support_status: str = "not_verified"
