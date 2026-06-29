from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import get_settings
from app.models.ai import ModelConfig


def model_config_response(config: ModelConfig) -> "ModelConfigResponse":
    runtime_kind, credential_status, readiness_label = _provider_readiness(config)
    return ModelConfigResponse(
        id=config.id,
        workspace_id=config.workspace_id,
        provider=config.provider,
        model=config.model,
        purpose=config.purpose,
        prompt_token_cost_per_1k=config.prompt_token_cost_per_1k,
        completion_token_cost_per_1k=config.completion_token_cost_per_1k,
        max_context_tokens=config.max_context_tokens,
        active=config.active,
        archived_at=config.archived_at,
        created_at=config.created_at,
        runtime_kind=runtime_kind,
        credential_status=credential_status,
        readiness_label=readiness_label,
    )


def _provider_readiness(config: ModelConfig) -> tuple[str, str, str]:
    provider = config.provider.strip().lower()
    if config.archived_at is not None:
        return "archived", "not_applicable", "Archived routes are excluded from runtime selection."
    if provider == "mock" or provider.startswith("mock"):
        return "mock", "not_required", "Deterministic local provider ready; no API key required."
    if provider in {"openai", "openai-compatible"}:
        if get_settings().openai_api_key:
            return "live", "configured", "Live provider credentials configured on the backend."
        return "live", "missing", "OPENAI_API_KEY is missing; calls will fail and be ledgered."
    return (
        "custom",
        "integration_required",
        "Custom provider route falls back to mock execution until integrated.",
    )


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
    runtime_kind: str = "mock"
    credential_status: str = "not_required"
    readiness_label: str = "Deterministic local provider ready; no API key required."


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
