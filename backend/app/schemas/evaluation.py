from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.evaluation import EvaluationMode, EvaluationRunStatus


class EvaluationRunRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    jsonl_cases: str = Field(min_length=1)
    modes: list[EvaluationMode] = Field(default_factory=lambda: [EvaluationMode.system_v1])
    agent_id: UUID | None = None

    @field_validator("name", "jsonl_cases")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped

    @field_validator("modes")
    @classmethod
    def modes_must_not_be_empty(cls, value: list[EvaluationMode]) -> list[EvaluationMode]:
        if not value:
            raise ValueError("modes cannot be empty")
        return value


class EvaluationCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    external_id: str
    language: str
    input_message: str
    expected_intent: str | None
    expected_route: str
    safety_risk: str
    max_prompt_tokens: int | None
    created_at: datetime


class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_case_id: UUID
    mode: str
    language: str
    actual_route: str
    answer: str | None
    citations_json: str
    passed: bool
    scores_json: str
    latency_ms: int
    prompt_tokens: int
    estimated_cost: float
    error_message: str | None
    created_at: datetime


class EvaluationMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    mode: str
    language: str
    metric_name: str
    metric_value: float
    created_at: datetime


class EvaluationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    modes_json: str
    status: EvaluationRunStatus
    total_cases: int
    created_by_user_id: UUID
    created_at: datetime
    completed_at: datetime | None


class EvaluationDetailResponse(BaseModel):
    run: EvaluationRunResponse
    results: list[EvaluationResultResponse]
    metrics: list[EvaluationMetricResponse]
