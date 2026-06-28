from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage, detect_language_for_messages
from app.models.agent import (
    Checkpoint,
    GraphRun,
    GraphRunStatus,
    GraphStep,
    GraphStepStatus,
    ToolCall,
)
from app.models.ai import AIRun
from app.services.guardrail_catalog_service import GuardrailCatalogService, GuardrailEffectivePolicy
from app.services.langchain_support import (
    CLASSIFICATION_TEMPLATE_TEXT,
    DRAFT_RESPONSE_TEMPLATE_TEXT,
    build_classification_prompt,
    build_draft_response_prompt,
    chunk_payloads_to_documents,
    create_search_documents_tool,
    run_classification_chain,
    run_draft_response_chain,
)
from app.services.model_config_service import ModelConfigService
from app.services.model_provider import ConfiguredModelProvider, ModelProviderError
from app.services.prompt_template_service import PromptTemplateService
from app.services.support_agent_state import SupportAgentState
from app.services.token_budget import ModelCallBudgetPlan, TokenBudgetPlanner
from app.services.tool_service import ToolService


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
        classification = _classification_analysis(state["input_message"])
        prompt_template = PromptTemplateService(self.db).get_active_or_create_default(
            workspace_id=UUID(state["workspace_id"]),
            name="support_intent_classifier",
            language=language,
            template_text=CLASSIFICATION_TEMPLATE_TEXT,
        )
        budget_plan = _plan_model_call(
            db=self.db,
            workspace_id=UUID(state["workspace_id"]),
            purpose="classification",
            fallback_model="mock-cheap",
            prompt_text=build_classification_prompt(state["input_message"]),
            completion_text=json.dumps(classification, ensure_ascii=False),
            language=language,
            model_config_id=_agent_model_config_id(state),
        )
        if not budget_plan.allowed:
            output = _budget_failure_output(state, budget_plan, purpose="classification")
            self._record_step(
                "classify_intent",
                state,
                output,
                started,
                status=GraphStepStatus.failed,
                error_message=output["model_budget_failure"],
            )
            return output
        try:
            ai_response = run_classification_chain(
                provider=ConfiguredModelProvider(self.db),
                workspace_id=UUID(state["workspace_id"]),
                language=language,
                input_message=state["input_message"],
                graph_run_id=UUID(state["graph_run_id"]),
                prompt_template=prompt_template,
                completion_text=json.dumps(classification, ensure_ascii=False),
                model_config_id=_agent_model_config_id(state),
            )
        except ModelProviderError as exc:
            output = _provider_failure_output(state, exc)
            self._record_step(
                "classify_intent",
                state,
                output,
                started,
                exc.ai_run.id if exc.ai_run else None,
                status=GraphStepStatus.failed,
                error_message=str(exc),
            )
            return output
        structured = ai_response.structured_output or classification
        output: SupportAgentState = {
            "intent": str(structured.get("intent") or ai_response.content),
            "sentiment": str(structured.get("sentiment") or "neutral"),
            "product_area": str(structured.get("product_area") or "general"),
            "safety_risk": str(structured.get("safety_risk") or "low"),
            "escalation_needed": bool(structured.get("escalation_needed", False)),
            "classification_confidence": float(structured.get("confidence") or 0.0),
            "classification_rationale": str(
                structured.get("rationale") or "Classified by support workflow."
            ),
        }
        self._record_step("classify_intent", state, output, started, ai_response.ai_run.id)
        return output

    def retrieve_evidence(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        language = SupportedLanguage(state["detected_language"])
        if state.get("model_provider_failure") or state.get("model_budget_failure"):
            output: SupportAgentState = {
                "retrieved_chunks": [],
                "citations": [],
                "no_source": True,
            }
            self._record_step("retrieve_evidence", state, output, started)
            return output
        workspace_id = UUID(state["workspace_id"])
        tool_definition = ToolService(self.db).get_tool_definition(
            workspace_id=workspace_id, tool_name="search_documents"
        )
        tool_input = {
            "query": state["input_message"],
            "language": language.value,
            "top_k": _retrieval_top_k(state),
            "min_score": _retrieval_threshold(state),
        }
        if not tool_definition.enabled:
            output = {
                "retrieved_chunks": [],
                "citations": [],
                "no_source": True,
                "langchain_tool": "search_documents",
                "tool_disabled": "search_documents",
                "errors": [
                    *state.get("errors", []),
                    "search_documents disabled by workspace tool configuration",
                ],
            }
            step = self._record_step(
                "retrieve_evidence",
                state,
                output,
                started,
                status=GraphStepStatus.failed,
                error_message="search_documents disabled by workspace tool configuration",
            )
            self.db.add(
                ToolCall(
                    workspace_id=workspace_id,
                    graph_run_id=UUID(state["graph_run_id"]),
                    graph_step_id=step.id,
                    tool_name="search_documents",
                    input_json=json.dumps(tool_input),
                    output_json=json.dumps(
                        {
                            "framework": tool_definition.framework,
                            "tool_disabled": True,
                            "no_source": True,
                            "result_count": 0,
                            "timeout_ms": tool_definition.timeout_ms,
                            "max_retries": tool_definition.max_retries,
                        }
                    ),
                    status=GraphStepStatus.failed,
                    latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
                )
            )
            self.db.commit()
            return output
        search_tool = create_search_documents_tool(db=self.db, workspace_id=workspace_id)
        tool_output = search_tool.invoke(tool_input)
        raw_chunks = tool_output["results"]
        documents = chunk_payloads_to_documents(raw_chunks)
        chunks = []
        for chunk_payload, document in zip(raw_chunks, documents, strict=True):
            chunk = dict(chunk_payload)
            chunk["langchain_document_metadata"] = document.metadata
            chunks.append(chunk)
        output: SupportAgentState = {
            "retrieved_chunks": chunks,
            "retrieval_trace_id": tool_output["trace_id"],
            "citations": [chunk["citation"] for chunk in chunks],
            "no_source": tool_output["no_source"],
            "langchain_tool": search_tool.name,
        }
        step = self._record_step("retrieve_evidence", state, output, started)
        tool_started = time.perf_counter()
        self.db.add(
            ToolCall(
                workspace_id=workspace_id,
                graph_run_id=UUID(state["graph_run_id"]),
                graph_step_id=step.id,
                tool_name="search_documents",
                input_json=json.dumps(tool_input),
                output_json=json.dumps(
                    {
                        "framework": tool_output["framework"],
                        "trace_id": tool_output["trace_id"],
                        "result_count": tool_output["result_count"],
                        "langchain_document_count": len(documents),
                        "no_source": tool_output["no_source"],
                        "timeout_ms": tool_definition.timeout_ms,
                        "max_retries": tool_definition.max_retries,
                    }
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
        if (
            state.get("model_provider_failure")
            or state.get("model_budget_failure")
            or not state.get("retrieved_chunks")
        ):
            output: SupportAgentState = {"draft_answer": None}
            self._record_step("draft_response", state, output, started)
            return output
        chunks = state.get("retrieved_chunks") or []
        completion = _mock_answer(
            language=language,
            intent=state.get("intent"),
            input_message=state["input_message"],
            chunks=chunks,
        )
        documents = chunk_payloads_to_documents(chunks)
        prompt_template = PromptTemplateService(self.db).get_active_or_create_default(
            workspace_id=UUID(state["workspace_id"]),
            name="support_response_drafter",
            language=language,
            template_text=DRAFT_RESPONSE_TEMPLATE_TEXT,
        )
        budget_documents, budget_plan, trimmed_count = _fit_draft_documents_to_budget(
            db=self.db,
            workspace_id=UUID(state["workspace_id"]),
            input_message=state["input_message"],
            language=language,
            documents=documents,
            completion_text=completion,
            model_config_id=_agent_model_config_id(state),
        )
        if not budget_plan.allowed:
            output = _budget_failure_output(state, budget_plan, purpose="draft_response")
            output["draft_answer"] = None
            self._record_step(
                "draft_response",
                state,
                output,
                started,
                status=GraphStepStatus.failed,
                error_message=output["model_budget_failure"],
            )
            return output
        if trimmed_count:
            chunks = chunks[: len(budget_documents)]
            documents = budget_documents
        try:
            ai_response = run_draft_response_chain(
                provider=ConfiguredModelProvider(self.db),
                workspace_id=UUID(state["workspace_id"]),
                language=language,
                input_message=state["input_message"],
                documents=budget_documents,
                graph_run_id=UUID(state["graph_run_id"]),
                prompt_template=prompt_template,
                completion_text=completion,
                model_config_id=_agent_model_config_id(state),
            )
        except ModelProviderError as exc:
            output = _provider_failure_output(state, exc)
            output["draft_answer"] = None
            self._record_step(
                "draft_response",
                state,
                output,
                started,
                exc.ai_run.id if exc.ai_run else None,
                status=GraphStepStatus.failed,
                error_message=str(exc),
            )
            return output
        output: SupportAgentState = {"draft_answer": ai_response.content}
        if trimmed_count:
            output.update(
                {
                    "retrieved_chunks": chunks,
                    "citations": [str(chunk.get("citation")) for chunk in chunks],
                    "token_budget_action": "trimmed_retrieved_context",
                    "trimmed_context_count": trimmed_count,
                }
            )
        self._record_step("draft_response", state, output, started, ai_response.ai_run.id)
        return output

    def score_confidence(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        if state.get("classification_confidence") is not None:
            confidence = float(state.get("classification_confidence") or 0.0)
        elif state.get("intent") in {"prompt_injection", "privacy_complaint"}:
            confidence = 0.2
        elif state.get("retrieved_chunks") and state.get("draft_answer"):
            confidence = 0.85
        else:
            confidence = 0.1
        output: SupportAgentState = {"confidence_score": confidence}
        self._record_step("score_confidence", state, output, started)
        return output

    def route_review_or_finalize(self, state: SupportAgentState) -> SupportAgentState:
        started = time.perf_counter()
        policies = GuardrailCatalogService(self.db).effective_policies(
            workspace_id=UUID(state["workspace_id"])
        )
        confidence_threshold = _confidence_threshold(state, policies)
        route_reasons = _route_reasons(state, confidence_threshold, policies)
        decision = "human_review" if route_reasons else "finalize"
        output: SupportAgentState = {
            "route_decision": decision,
            "route_reasons": route_reasons,
            "confidence_threshold": confidence_threshold,
        }
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
        status: GraphStepStatus = GraphStepStatus.succeeded,
        error_message: str | None = None,
    ) -> GraphStep:
        workspace_id = UUID(input_state["workspace_id"])
        graph_run_id = UUID(input_state["graph_run_id"])
        parent_span_id = self._latest_span_id(
            workspace_id=workspace_id, graph_run_id=graph_run_id
        )
        step = GraphStep(
            workspace_id=workspace_id,
            graph_run_id=graph_run_id,
            parent_span_id=parent_span_id,
            step_name=step_name,
            input_json=json.dumps(_compact_state(input_state), ensure_ascii=False, default=str),
            output_json=json.dumps(output, ensure_ascii=False, default=str),
            status=status,
            latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
            ai_run_id=ai_run_id,
            error_message=error_message,
            retry_count=0,
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        if ai_run_id is not None:
            self._attach_ai_run_to_step(ai_run_id=ai_run_id, step=step)
        self._record_checkpoint(
            step_name=step_name,
            input_state=input_state,
            output=output,
            status=status,
            error_message=error_message,
        )
        return step

    def _record_checkpoint(
        self,
        *,
        step_name: str,
        input_state: SupportAgentState,
        output: SupportAgentState,
        status: GraphStepStatus,
        error_message: str | None,
    ) -> None:
        checkpoint = Checkpoint(
            workspace_id=UUID(input_state["workspace_id"]),
            graph_run_id=UUID(input_state["graph_run_id"]),
            checkpoint_key=f"{step_name}:after",
            state_json=json.dumps(
                _checkpoint_snapshot(
                    step_name=step_name,
                    input_state=input_state,
                    output=output,
                    status=status,
                    error_message=error_message,
                ),
                ensure_ascii=False,
                default=str,
            ),
        )
        self.db.add(checkpoint)
        self.db.commit()

    def _attach_ai_run_to_step(self, *, ai_run_id: UUID, step: GraphStep) -> None:
        ai_run = self.db.get(AIRun, ai_run_id)
        if ai_run is None or ai_run.workspace_id != step.workspace_id:
            return
        ai_run.graph_run_id = step.graph_run_id
        ai_run.graph_step_id = step.id
        step.token_count = ai_run.total_tokens
        step.estimated_cost = ai_run.estimated_cost
        self.db.commit()
        self.db.refresh(step)

    def _latest_span_id(self, *, workspace_id: UUID, graph_run_id: UUID) -> str | None:
        previous_step = self.db.scalar(
            select(GraphStep)
            .where(
                GraphStep.workspace_id == workspace_id,
                GraphStep.graph_run_id == graph_run_id,
            )
            .order_by(GraphStep.created_at.desc(), GraphStep.id.desc())
        )
        return previous_step.span_id if previous_step else None


def _plan_model_call(
    *,
    db: Session,
    workspace_id: UUID,
    purpose: str,
    fallback_model: str,
    prompt_text: str,
    completion_text: str,
    language: SupportedLanguage,
    model_config_id: UUID | None = None,
) -> ModelCallBudgetPlan:
    pricing = ModelConfigService(db).resolve_pricing(
        workspace_id=workspace_id,
        purpose=purpose,
        fallback_model=fallback_model,
        model_config_id=model_config_id,
    )
    return TokenBudgetPlanner().plan_model_call(
        prompt_text=prompt_text,
        completion_text=completion_text,
        language=language,
        pricing=pricing,
    )


def _fit_draft_documents_to_budget(
    *,
    db: Session,
    workspace_id: UUID,
    input_message: str,
    language: SupportedLanguage,
    documents: list,
    completion_text: str,
    model_config_id: UUID | None = None,
) -> tuple[list, ModelCallBudgetPlan, int]:
    current_documents = list(documents)
    trimmed_count = 0
    while True:
        prompt_text = build_draft_response_prompt(
            input_message=input_message, language=language, documents=current_documents
        )
        plan = _plan_model_call(
            db=db,
            workspace_id=workspace_id,
            purpose="draft_response",
            fallback_model="mock-standard",
            prompt_text=prompt_text,
            completion_text=completion_text,
            language=language,
            model_config_id=model_config_id,
        )
        if plan.allowed or not current_documents:
            return current_documents, plan, trimmed_count
        current_documents = current_documents[:-1]
        trimmed_count += 1


def _classification_analysis(input_message: str) -> dict:
    text = input_message.lower()
    if _has_prompt_injection(text):
        return {
            "intent": "prompt_injection",
            "sentiment": "urgent",
            "product_area": "security",
            "safety_risk": "high",
            "escalation_needed": True,
            "confidence": 0.96,
            "rationale": "The message asks the system to ignore or reveal instructions.",
        }
    if any(term in text for term in ["privacy", "個人情報", "个人信息", "泄露"]):
        return {
            "intent": "privacy_complaint",
            "sentiment": "angry",
            "product_area": "privacy",
            "safety_risk": "high",
            "escalation_needed": True,
            "confidence": 0.9,
            "rationale": "The customer reports possible personal-data exposure or privacy harm.",
        }
    if any(term in text for term in ["security", "login", "ログイン", "端末", "安全"]):
        return {
            "intent": "account_security",
            "sentiment": "urgent",
            "product_area": "security",
            "safety_risk": "medium",
            "escalation_needed": False,
            "confidence": 0.82,
            "rationale": "The request is about account access or security-sensitive activity.",
        }
    if any(term in text for term in ["refund", "返金", "退款"]):
        return {
            "intent": "refund_request",
            "sentiment": "neutral",
            "product_area": "billing",
            "safety_risk": "low",
            "escalation_needed": False,
            "confidence": 0.88,
            "rationale": "The customer is asking about refund eligibility or process.",
        }
    return {
        "intent": "general_support",
        "sentiment": "neutral",
        "product_area": "general",
        "safety_risk": "low",
        "escalation_needed": False,
        "confidence": 0.55,
        "rationale": "The message does not match a specialized support category.",
    }


def _budget_failure_output(
    state: SupportAgentState, plan: ModelCallBudgetPlan, *, purpose: str
) -> SupportAgentState:
    message = (
        f"token_budget_exceeded: {purpose} requested {plan.total_tokens} tokens "
        f"but {plan.model} allows {plan.max_context_tokens}"
    )
    errors = [*state.get("errors", []), message]
    return {
        "model_budget_failure": message,
        "errors": errors,
        "confidence_score": 0.0,
        "route_decision": "human_review",
    }


def _provider_failure_output(
    state: SupportAgentState, exc: ModelProviderError
) -> SupportAgentState:
    message = str(exc)
    errors = [*state.get("errors", []), message]
    return {
        "model_provider_failure": message,
        "errors": errors,
        "confidence_score": 0.0,
        "route_decision": "human_review",
    }


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


def _checkpoint_snapshot(
    *,
    step_name: str,
    input_state: SupportAgentState,
    output: SupportAgentState,
    status: GraphStepStatus,
    error_message: str | None,
) -> dict:
    merged_state: SupportAgentState = {**input_state, **output}
    snapshot = _compact_state(merged_state)
    retrieved_chunks = merged_state.get("retrieved_chunks") or []
    citations = merged_state.get("citations") or []
    snapshot["checkpoint"] = {
        "completed_step": step_name,
        "status": status.value,
        "error_message": error_message,
        "state_keys": sorted(str(key) for key in merged_state.keys()),
        "retrieved_chunk_count": len(retrieved_chunks) if isinstance(retrieved_chunks, list) else 0,
        "citation_count": len(citations) if isinstance(citations, list) else 0,
        "has_draft_answer": bool(merged_state.get("draft_answer")),
        "has_final_answer": bool(merged_state.get("final_answer")),
    }
    return snapshot


def _compact_state(state: SupportAgentState) -> dict:
    allowed = [
        "input_message",
        "detected_language",
        "intent",
        "retrieval_trace_id",
        "sentiment",
        "product_area",
        "safety_risk",
        "escalation_needed",
        "classification_confidence",
        "classification_rationale",
        "draft_answer",
        "confidence_score",
        "route_decision",
        "route_reasons",
        "final_answer",
        "citations",
        "no_source",
        "model_provider_failure",
        "model_budget_failure",
        "token_budget_action",
        "trimmed_context_count",
        "confidence_threshold",
        "agent_token_budget",
        "agent_model_config_id",
        "agent_settings",
        "langchain_tool",
        "tool_disabled",
        "errors",
    ]
    return {key: state.get(key) for key in allowed if key in state}


def _agent_model_config_id(state: SupportAgentState) -> UUID | None:
    raw_value = state.get("agent_model_config_id")
    if not raw_value:
        return None
    return UUID(str(raw_value))


def _route_reasons(
    state: SupportAgentState,
    confidence_threshold: float,
    policies: dict[str, GuardrailEffectivePolicy],
) -> list[str]:
    checks = {
        "model_provider_failure": bool(state.get("model_provider_failure")),
        "model_budget_failure": bool(state.get("model_budget_failure")),
        "confidence_threshold": state.get("confidence_score", 0) < confidence_threshold,
        "prompt_injection": state.get("intent") == "prompt_injection",
        "privacy_complaint": state.get("intent") == "privacy_complaint",
        "high_safety_risk": state.get("safety_risk") == "high",
        "escalation_needed": bool(state.get("escalation_needed")),
        "citation_required": not bool(state.get("citations")),
        "unsupported_answer": bool(state.get("no_source")),
    }
    return [
        guardrail_type
        for guardrail_type, failed in checks.items()
        if failed and _policy_routes_to_review(policies.get(guardrail_type))
    ]


def _policy_routes_to_review(policy: GuardrailEffectivePolicy | None) -> bool:
    if policy is None:
        return True
    return policy.enabled and policy.action_on_fail == "route_to_human_review"


def _retrieval_top_k(state: SupportAgentState) -> int:
    value = _agent_settings(state).get("retrieval_top_k")
    if isinstance(value, int):
        return min(8, max(1, value))
    return 4


def _retrieval_threshold(state: SupportAgentState) -> float:
    configured = _agent_settings(state).get("retrieval_min_score")
    if isinstance(configured, int | float):
        return min(1.0, max(0.0, float(configured)))
    intent = state.get("intent")
    if intent in {"prompt_injection", "privacy_complaint"}:
        return 0.35
    if intent == "general_support":
        return 0.45
    return 0.2


def _confidence_threshold(
    state: SupportAgentState, policies: dict[str, GuardrailEffectivePolicy] | None = None
) -> float:
    policy_threshold = (policies or {}).get("confidence_threshold")
    if policy_threshold and policy_threshold.threshold is not None:
        return min(0.95, max(0.1, float(policy_threshold.threshold)))
    configured = _agent_settings(state).get("confidence_threshold")
    if isinstance(configured, int | float):
        return min(0.95, max(0.1, float(configured)))
    return 0.5


def _agent_settings(state: SupportAgentState) -> dict:
    settings = state.get("agent_settings") or {}
    return settings if isinstance(settings, dict) else {}


def _has_prompt_injection(text: str) -> bool:
    return any(
        marker in text
        for marker in [
            "ignore previous instructions",
            "ignore all previous instructions",
            "ignore all instructions",
            "system prompt",
            "developer message",
            "reveal private",
            "private workspace",
            "プロンプトを無視",
            "忽略之前的指示",
        ]
    )


def _mock_answer(
    *,
    language: SupportedLanguage,
    intent: str | None,
    input_message: str,
    chunks: list[dict],
) -> str:
    evidence = " ".join(str(chunk.get("content", "")) for chunk in chunks[:2])
    combined = f"{input_message} {evidence}".lower()
    if language == SupportedLanguage.ja:
        if intent == "account_security" or any(
            term in combined for term in ["ログイン", "端末", "パスワード"]
        ):
            return (
                "関連資料によると、すぐにパスワードを変更し、"
                "すべての端末からログアウトし、二要素認証を有効にしてください。"
            )
        if intent == "refund_request":
            return (
                "関連資料によると、返金は購入から30日以内に申請できます。"
                "31日目以降は例外として人間の担当者が確認します。"
            )
        return "関連資料に基づき、人間のサポート担当者が確認できる範囲で対応します。"
    if language == SupportedLanguage.zh:
        if intent == "privacy_complaint" or any(
            term in combined for term in ["个人信息", "泄露", "隐私"]
        ):
            return (
                "根据相关政策，个人信息泄露投诉必须升级给隐私与安全团队进行人工审核，"
                "不能透露内部调查细节。"
            )
        if intent == "refund_request":
            return "根据相关资料，购买后30天内可以申请退款。超过期限的情况需要人工审核。"
        return "根据相关资料，支持团队会在有依据的范围内处理该请求。"
    if intent == "account_security" or any(
        term in combined for term in ["login", "security", "password"]
    ):
        return (
            "According to the account security guide, change your password, "
            "sign out of all devices, and enable two-factor authentication immediately."
        )
    if intent == "refund_request":
        if any(term in combined for term in ["partial", "duplicate", "enterprise", "upgrade"]):
            return (
                "According to the retrieved policy, refunds are available within 30 days, "
                "and partial refunds may be reviewed for duplicate enterprise purchases "
                "in the same billing cycle."
            )
        return "According to the retrieved policy, refunds can be requested within 30 days."
    return (
        "The retrieved support policy does not provide enough detail for a final answer; "
        "a human review is recommended."
    )
