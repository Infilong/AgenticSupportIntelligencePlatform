from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID | None
    provider: str
    model: str
    purpose: str
    prompt_token_cost_per_1k: float
    completion_token_cost_per_1k: float
    max_context_tokens: int
    active: bool
    archived_at: datetime | None
    created_at: datetime


class ModelConfigListResponse(BaseModel):
    items: list[ModelConfigResponse]
    total: int
    limit: int | None
    offset: int
    has_next: bool


class ModelConfigCreateRequest(BaseModel):
    provider: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=120)
    purpose: str = Field(min_length=1, max_length=80)
    prompt_token_cost_per_1k: float = Field(ge=0)
    completion_token_cost_per_1k: float = Field(ge=0)
    max_context_tokens: int = Field(ge=256, le=2_000_000)
    active: bool = True

    @field_validator("provider", "model", "purpose")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped
