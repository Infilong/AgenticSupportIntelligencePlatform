from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ToolUsageSummaryResponse(BaseModel):
    total_calls: int
    failed_calls: int
    average_latency_ms: float
    last_used_at: datetime | None


class ToolCallSummaryResponse(BaseModel):
    id: UUID
    graph_run_id: UUID
    graph_step_id: UUID
    status: str
    latency_ms: int
    result_summary: str
    created_at: datetime


class ToolConfigUpdateRequest(BaseModel):
    enabled: bool | None = None
    timeout_ms: int | None = Field(default=None, ge=100, le=120_000)
    max_retries: int | None = Field(default=None, ge=0, le=5)


class ToolCatalogItemResponse(BaseModel):
    name: str
    description: str
    framework: str
    enabled: bool
    permissions: list[str]
    timeout_ms: int | None
    max_retries: int
    retry_policy: str
    input_schema: dict[str, object] = Field(default_factory=dict)
    output_schema: dict[str, object] = Field(default_factory=dict)
    related_workflow_nodes: list[str]
    usage: ToolUsageSummaryResponse
    recent_calls: list[ToolCallSummaryResponse]
