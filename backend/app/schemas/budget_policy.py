from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetPolicyUpdateRequest(BaseModel):
    monthly_token_budget: int = Field(ge=1_000, le=100_000_000)
    monthly_cost_budget: float = Field(ge=0.01, le=1_000_000)
    per_run_token_budget: int = Field(ge=500, le=32000)
    per_run_cost_budget: float = Field(ge=0.001, le=10_000)
    rate_limit_requests_per_hour: int = Field(ge=1, le=100_000)
    alert_threshold_percent: float = Field(ge=0.1, le=1.0)


class BudgetPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    monthly_token_budget: int
    monthly_cost_budget: float
    per_run_token_budget: int
    per_run_cost_budget: float
    rate_limit_requests_per_hour: int
    alert_threshold_percent: float
    created_at: datetime
    updated_at: datetime
