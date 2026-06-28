from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.model_config import ModelConfigResponse


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    token_budget: int = Field(default=4000, ge=500, le=32000)
    model_config_id: UUID | None = None
    folder_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class AgentFolderUpdateRequest(BaseModel):
    folder_id: UUID | None = None


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    active: bool | None = None
    token_budget: int | None = Field(default=None, ge=500, le=32000)
    confidence_threshold: float | None = Field(default=None, ge=0.1, le=0.95)
    retrieval_top_k: int | None = Field(default=None, ge=1, le=8)
    retrieval_min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    model_config_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def strip_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class AgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    active: bool
    model_config_id: UUID | None
    folder_id: UUID | None
    token_budget: int
    settings_json: str
    archived_at: datetime | None
    created_at: datetime


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    total: int
    limit: int | None
    offset: int
    has_next: bool


class AgentRunRequest(BaseModel):
    input_message: str = Field(min_length=1, max_length=4000)

    @field_validator("input_message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("input_message cannot be blank")
        return stripped


class GraphRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    agent_config_id: UUID
    user_id: UUID
    input_message: str
    trace_id: str | None
    language: str | None
    status: str
    route_decision: str | None
    final_answer: str | None
    created_at: datetime
    completed_at: datetime | None


class AgentOperationalSummaryResponse(BaseModel):
    agent: AgentResponse
    assigned_model_config: ModelConfigResponse | None
    recent_runs: list[GraphRunResponse]
    total_runs: int
    completed_runs: int
    human_review_runs: int
    failed_runs: int
    total_tokens: int
    total_estimated_cost: float
    average_ai_latency_ms: float | None
    last_run_at: datetime | None
    evaluation_runs: int
    evaluation_result_count: int
    failed_evaluation_results: int
    evaluation_pass_rate: float | None
    last_evaluation_at: datetime | None


class RuntimeComponentResponse(BaseModel):
    name: str
    framework: str
    role: str


class WorkflowEdgeResponse(BaseModel):
    source: str
    target: str
    condition: str | None = None
    label: str


class WorkflowNodeFailureResponse(BaseModel):
    graph_run_id: UUID
    graph_step_id: UUID
    error_message: str | None
    latency_ms: int
    created_at: datetime


class WorkflowNodeResponse(BaseModel):
    name: str
    order: int
    role: str
    runtime_framework: str
    uses_langchain: bool
    expected_state_keys: list[str]
    run_count: int
    failure_count: int
    average_latency_ms: float | None
    total_tokens: int
    estimated_cost: float
    last_executed_at: datetime | None
    recent_failures: list[WorkflowNodeFailureResponse]


class AgentWorkflowSummaryResponse(BaseModel):
    agent: AgentResponse
    runtime: GraphRuntimeResponse
    nodes: list[WorkflowNodeResponse]
    edges: list[WorkflowEdgeResponse]


class GraphRuntimeResponse(BaseModel):
    orchestrator: str
    state_schema: str
    graph_builder: str
    execution_mode: str
    node_count: int
    conditional_routes: list[str]
    persistence: list[str]
    langchain_components: list[RuntimeComponentResponse]


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tool_name: str
    input_json: str
    output_json: str
    status: str
    latency_ms: int
    created_at: datetime
    framework: str | None = None


class AIRunTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model: str
    model_config_id: UUID | None
    purpose: str
    language: str
    prompt_template_id: UUID | None
    prompt_template_name: str | None = None
    prompt_template_text: str | None = None
    prompt_version: int | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_ms: int
    cache_hit: bool
    status: str
    error_message: str | None
    created_at: datetime


class GuardrailTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    graph_step_id: UUID | None
    guardrail_type: str
    passed: bool
    severity: str
    message: str
    created_at: datetime


class CheckpointTraceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    graph_run_id: UUID
    checkpoint_key: str
    state_json: str
    created_at: datetime


class GraphStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    span_id: str | None
    parent_span_id: str | None
    step_name: str
    input_json: str
    output_json: str
    status: str
    latency_ms: int
    ai_run_id: UUID | None
    token_count: int | None
    estimated_cost: float | None
    error_message: str | None
    retry_count: int
    created_at: datetime
    tool_calls: list[ToolCallResponse]
    ai_run: AIRunTraceResponse | None = None
    runtime_framework: str | None = None
    node_role: str | None = None
    uses_langchain: bool = False
    state_keys: list[str] = Field(default_factory=list)


class GraphTraceResponse(BaseModel):
    runtime: GraphRuntimeResponse
    run: GraphRunResponse
    steps: list[GraphStepResponse]
    ai_runs: list[AIRunTraceResponse]
    guardrails: list[GuardrailTraceResponse]
    checkpoints: list[CheckpointTraceResponse]
