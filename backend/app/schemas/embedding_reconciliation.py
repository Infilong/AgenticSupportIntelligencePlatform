from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.ai import AIRunStatus


class EmbeddingReconcileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmed_tokens: int = Field(strict=True, ge=0, le=2_147_483_647)
    evidence_reference: str = Field(min_length=1, max_length=240)

    @field_validator("evidence_reference")
    @classmethod
    def nonblank_reference(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A billing evidence reference is required")
        return value.strip()


class EmbeddingAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    graph_run_id: UUID | None
    execution_id: UUID | None = None
    execution_protocol: str | None = None
    model: str
    purpose: str
    status: AIRunStatus
    total_tokens: int
    estimated_cost: float
    error_message: str | None
    created_at: datetime


class EmbeddingAttemptList(BaseModel):
    items: list[EmbeddingAttemptResponse]
    has_more: bool


class EmbeddingRecoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=240)

    @field_validator("reason")
    @classmethod
    def nonblank_reason(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A recovery reason is required")
        return value.strip()
