from typing_extensions import TypedDict


class SupportAgentState(TypedDict, total=False):
    workspace_id: str
    user_id: str
    agent_config_id: str
    agent_model_config_id: str | None
    graph_run_id: str
    input_message: str
    agent_token_budget: int
    agent_settings: dict
    detected_language: str
    intent: str
    sentiment: str
    product_area: str
    safety_risk: str
    escalation_needed: bool
    classification_confidence: float
    classification_rationale: str
    retrieved_chunks: list[dict]
    retrieval_trace_id: str | None
    langchain_tool: str
    draft_answer: str | None
    confidence_score: float
    confidence_threshold: float
    route_decision: str
    route_reasons: list[str]
    final_answer: str | None
    citations: list[str]
    errors: list[str]
    model_provider_failure: str | None
    trimmed_context_count: int
    token_budget_action: str | None
    model_budget_failure: str | None
