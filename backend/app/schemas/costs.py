from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CostPurposeSummaryResponse(BaseModel):
    purpose: str
    runs: int
    tokens: int
    estimated_cost: float


class CostModelSummaryResponse(BaseModel):
    provider: str
    model: str
    runs: int
    tokens: int
    estimated_cost: float


class CostAgentSummaryResponse(BaseModel):
    agent_id: UUID
    agent_name: str
    graph_runs: int
    model_calls: int
    tokens: int
    estimated_cost: float
    average_latency_ms: float


class CostRunSummaryResponse(BaseModel):
    graph_run_id: UUID
    agent_name: str
    status: str
    route_decision: str | None
    model_calls: int
    tokens: int
    estimated_cost: float
    latency_ms: int
    created_at: datetime


class RecentAIRunSummaryResponse(BaseModel):
    id: UUID
    graph_run_id: UUID | None
    provider: str
    model: str
    purpose: str
    language: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_ms: int
    cache_hit: bool
    status: str
    error_message: str | None
    created_at: datetime


class CostSummaryResponse(BaseModel):
    workspace_id: UUID
    total_runs: int
    total_tokens: int
    total_estimated_cost: float
    average_latency_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    cache_hit_rate: float
    failed_ai_runs: int
    by_purpose: list[CostPurposeSummaryResponse]
    by_model: list[CostModelSummaryResponse]
    by_agent: list[CostAgentSummaryResponse]
    recent_runs: list[CostRunSummaryResponse]
    recent_ai_runs: list[RecentAIRunSummaryResponse]
