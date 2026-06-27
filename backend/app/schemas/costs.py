from uuid import UUID

from pydantic import BaseModel


class CostPurposeSummaryResponse(BaseModel):
    purpose: str
    runs: int
    tokens: int
    estimated_cost: float


class CostSummaryResponse(BaseModel):
    workspace_id: UUID
    total_runs: int
    total_tokens: int
    total_estimated_cost: float
    average_latency_ms: float
    cache_hit_rate: float
    by_purpose: list[CostPurposeSummaryResponse]
