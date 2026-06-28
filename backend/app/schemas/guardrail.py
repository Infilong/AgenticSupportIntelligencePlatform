from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GuardrailUsageSummaryResponse(BaseModel):
    total_evaluations: int
    failed_evaluations: int
    pass_rate: float
    last_failed_at: datetime | None


class GuardrailFailureResponse(BaseModel):
    id: UUID
    graph_run_id: UUID
    graph_step_id: UUID | None
    severity: str
    message: str
    created_at: datetime


class GuardrailPolicyUpdateRequest(BaseModel):
    enabled: bool = True
    severity: str = Field(default="medium", min_length=1, max_length=20)
    action_on_fail: str = Field(default="route_to_human_review", min_length=1, max_length=80)
    threshold: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"low", "medium", "high"}:
            raise ValueError("severity must be low, medium, or high")
        return normalized

    @field_validator("action_on_fail")
    @classmethod
    def validate_action_on_fail(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"route_to_human_review", "record_only"}:
            raise ValueError("action_on_fail must be route_to_human_review or record_only")
        return normalized


class GuardrailCatalogItemResponse(BaseModel):
    guardrail_type: str
    label: str
    description: str
    stage: str
    enabled: bool
    configurable: bool
    default_severity: str
    severity: str
    action_on_fail: str
    threshold: float | None
    related_workflow_nodes: list[str]
    usage: GuardrailUsageSummaryResponse
    recent_failures: list[GuardrailFailureResponse]
