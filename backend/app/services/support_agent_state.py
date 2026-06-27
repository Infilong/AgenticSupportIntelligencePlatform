from typing_extensions import TypedDict


class SupportAgentState(TypedDict, total=False):
    workspace_id: str
    user_id: str
    agent_config_id: str
    graph_run_id: str
    input_message: str
    detected_language: str
    intent: str
    retrieved_chunks: list[dict]
    retrieval_trace_id: str | None
    draft_answer: str | None
    confidence_score: float
    route_decision: str
    final_answer: str | None
    citations: list[str]
    errors: list[str]
