from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AgentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    token_budget: int = Field(default=4000, ge=500, le=32000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be blank")
        return stripped


class AgentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    active: bool | None = None
    token_budget: int | None = Field(default=None, ge=500, le=32000)
    confidence_threshold: float | None = Field(default=None, ge=0.1, le=0.95)
    retrieval_top_k: int | None = Field(default=None, ge=1, le=8)
    retrieval_min_score: float | None = Field(default=None, ge=0.0, le=1.0)

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
    token_budget: int
    settings_json: str
    created_at: datetime


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
    language: str | None
    status: str
    route_decision: str | None
    final_answer: str | None
    created_at: datetime
    completed_at: datetime | None


class RuntimeComponentResponse(BaseModel):
    name: str
    framework: str
    role: str


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
