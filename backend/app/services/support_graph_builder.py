"""Graph topology and optional worker admission at each node boundary."""

from langgraph.graph import END, START, StateGraph

from app.services.input_clarification import (
    needs_input_clarification,
    request_input_clarification,
)
from app.services.support_agent_state import SupportAgentState


def run_support_graph(runner, state: SupportAgentState, *, before_node=None) -> SupportAgentState:
    names = ["detect_language", "classify_intent", "retrieve_evidence", "compress_context",
             "draft_response", "score_confidence", "route_review_or_finalize", "finalize_response"]
    graph = StateGraph(SupportAgentState)

    def guarded(name):
        def invoke(state: SupportAgentState):
            if before_node is not None:
                before_node(name)
            return getattr(runner, name)(state)
        return invoke

    for name in names:
        graph.add_node(name, guarded(name))
    def clarify(state):
        if before_node is not None:
            before_node("request_clarification")
        return request_input_clarification(runner, state)

    graph.add_node("request_clarification", clarify)
    graph.add_conditional_edges(START,
        lambda current: "clarify" if needs_input_clarification(current) else "process",
        {"clarify": "request_clarification", "process": "detect_language"})
    graph.add_edge("detect_language", "classify_intent")
    graph.add_edge("request_clarification", END)
    for source, target in zip(names[1:6], names[2:7], strict=True):
        graph.add_edge(source, target)
    graph.add_conditional_edges("route_review_or_finalize", runner.route_after_decision,
                                {"finalize": "finalize_response", "human_review": END})
    graph.add_edge("finalize_response", END)
    return graph.compile().invoke(state)
