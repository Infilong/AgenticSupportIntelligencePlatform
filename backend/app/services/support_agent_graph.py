from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage, detect_language_for_messages
from app.models.agent import GraphRun, GraphRunStatus, GraphStep, GraphStepStatus, ToolCall
from app.services.model_provider import MockModelProvider
from app.services.retrieval_service import RetrievalService
from app.services.support_agent_state import SupportAgentState


class SupportAgentGraphRunner:
    def __init__(self, db: Session):
        self.db = db

    def run(self, initial_state: SupportAgentState) -> SupportAgentState:
        graph = StateGraph(SupportAgentState)
        graph.add_node("detect_language", self.detect_language)
        graph.add_node("classify_intent", self.classify_intent)
        graph.add_node("retrieve_evidence", self.retrieve_evidence)
        graph.add_node("draft_response", self.draft_response)
        graph.add_node("score_confidence", self.score_confidence)
        graph.add_node("route_review_or_finalize", self.route_review_or_finalize)
        graph.add_node("finalize_response", self.finalize_response)
        graph.add_edge(START, "detect_language")
        graph.add_edge("detect_language", "classify_intent")
        graph.add_edge("classify_intent", "retrieve_evidence")
        graph.add_edge("retrieve_evidence", "draft_response")
        graph.add_edge("draft_response", "score_confidence")
        graph.add_edge("score_confidence", "route_review_or_finalize")
        graph.add_conditional_edges(
            "route_review_or_finalize",
            self.route_after_decision,
            {"finalize": "finalize_response", "human_review": END},
        )
        graph.add_edge("finalize_response", END)
        return graph.compile().invoke(initial_state)

    def detect_language(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        language = detect_language_for_messages([state["input_message"]]).value
        output: SupportAgentState = {"detected_language": language}
        self._record_step("detect_language", state, output, started)
        return output

    def classify_intent(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        language = SupportedLanguage(state["detected_language"])
        text = state["input_message"].lower()
        if any(term in text for term in ["refund", "返金", "退款"]):
            intent = "refund_request"
        elif any(term in text for term in ["privacy", "個人情報", "个人信息"]):
            intent = "privacy_complaint"
        else:
            intent = "general_support"
        ai_response = MockModelProvider(self.db).complete(
            workspace_id=UUID(state["workspace_id"]),
            purpose="classification",
            language=language,
            prompt=f"Classify support intent: {state['input_message']}",
            model="mock-cheap",
            completion_text=intent,
        )
        output: SupportAgentState = {"intent": intent}
        self._record_step("classify_intent", state, output, started, ai_response.ai_run.id)
        return output

    def retrieve_evidence(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        language = SupportedLanguage(state["detected_language"])
        retrieval = RetrievalService(self.db).search(
            workspace_id=UUID(state["workspace_id"]),
            query=state["input_message"],
            language=language,
            top_k=4,
            min_score=0.2,
            document_id=None,
        )
        chunks = [result.__dict__ for result in retrieval.results]
        output: SupportAgentState = {
            "retrieved_chunks": chunks,
            "retrieval_trace_id": str(retrieval.trace_id),
            "citations": [result.citation for result in retrieval.results],
        }
        step = self._record_step("retrieve_evidence", state, output, started)
        tool_started = time.perf_counter()
        self.db.add(
            ToolCall(
                workspace_id=UUID(state["workspace_id"]),
                graph_run_id=UUID(state["graph_run_id"]),
                graph_step_id=step.id,
                tool_name="search_documents",
                input_json=json.dumps(
                    {"query": state["input_message"], "language": language.value}
                ),
                output_json=json.dumps(
                    {"trace_id": str(retrieval.trace_id), "result_count": len(retrieval.results)}
                ),
                status=GraphStepStatus.succeeded,
                latency_ms=max(1, int((time.perf_counter() - tool_started) * 1000)),
            )
        )
        self.db.commit()
        return output

    def draft_response(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        language = SupportedLanguage(state["detected_language"])
        if not state.get("retrieved_chunks"):
            output: SupportAgentState = {"draft_answer": None}
            self._record_step("draft_response", state, output, started)
            return output
        completion = _mock_answer(language)
        ai_response = MockModelProvider(self.db).complete(
            workspace_id=UUID(state["workspace_id"]),
            purpose="draft_response",
            language=language,
            prompt="Draft a grounded response using retrieved citations.",
            model="mock-standard",
            completion_text=completion,
        )
        output: SupportAgentState = {"draft_answer": completion}
        self._record_step("draft_response", state, output, started, ai_response.ai_run.id)
        return output

    def score_confidence(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        confidence = 0.85 if state.get("retrieved_chunks") and state.get("draft_answer") else 0.1
        output: SupportAgentState = {"confidence_score": confidence}
        self._record_step("score_confidence", state, output, started)
        return output

    def route_review_or_finalize(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        decision = "finalize" if state.get("confidence_score", 0) >= 0.5 else "human_review"
        output: SupportAgentState = {"route_decision": decision}
        self._record_step("route_review_or_finalize", state, output, started)
        return output

    def finalize_response(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        output: SupportAgentState = {"final_answer": state.get("draft_answer")}
        self._record_step("finalize_response", state, output, started)
        return output

    def route_after_decision(self, state: SupportAgentState) -> str:
        return state.get("route_decision", "human_review")

    def _record_step(
        self,
        step_name: str,
        input_state: SupportAgentState,
        output: SupportAgentState,
        started: float,
        ai_run_id: UUID | None = None,
    ) -> GraphStep:
        step = GraphStep(
            workspace_id=UUID(input_state["workspace_id"]),
            graph_run_id=UUID(input_state["graph_run_id"]),
            step_name=step_name,
            input_json=json.dumps(_compact_state(input_state), ensure_ascii=False, default=str),
            output_json=json.dumps(output, ensure_ascii=False, default=str),
            status=GraphStepStatus.succeeded,
            latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
            ai_run_id=ai_run_id,
            retry_count=0,
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step


def complete_graph_run(db: Session, graph_run: GraphRun, state: SupportAgentState) -> GraphRun:
    graph_run.language = state.get("detected_language")
    graph_run.route_decision = state.get("route_decision")
    graph_run.final_answer = state.get("final_answer")
    graph_run.status = (
        GraphRunStatus.completed
        if state.get("route_decision") == "finalize"
        else GraphRunStatus.needs_human_review
    )
    graph_run.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(graph_run)
    return graph_run


def _compact_state(state: SupportAgentState) -> dict:
    allowed = [
        "input_message",
        "detected_language",
        "intent",
        "retrieval_trace_id",
        "draft_answer",
        "confidence_score",
        "route_decision",
        "final_answer",
        "citations",
    ]
    return {key: state.get(key) for key in allowed if key in state}


def _mock_answer(language: SupportedLanguage) -> str:
    if language == SupportedLanguage.ja:
        return "関連資料によると、返金は30日以内に申請できます。"
    if language == SupportedLanguage.zh:
        return "根据相关资料，退款可以在30天内申请。"
    return "According to the retrieved policy, refunds can be requested within 30 days."
