from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


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


class GuardrailCatalogItemResponse(BaseModel):
    guardrail_type: str
    label: str
    description: str
    stage: str
    enabled: bool
    configurable: bool
    default_severity: str
    action_on_fail: str
    related_workflow_nodes: list[str]
    usage: GuardrailUsageSummaryResponse
    recent_failures: list[GuardrailFailureResponse]
