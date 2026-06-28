from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import detect_language
from app.models.review import GuardrailResult
from app.services.guardrail_catalog_service import GuardrailCatalogService, GuardrailEffectivePolicy
from app.services.support_agent_state import SupportAgentState


@dataclass(frozen=True)
class GuardrailDecision:
    guardrail_type: str
    passed: bool
    severity: str
    message: str
    action_on_fail: str = "route_to_human_review"


PROMPT_INJECTION_MARKERS = [
    "ignore previous instructions",
    "ignore all instructions",
    "system prompt",
    "developer message",
    "プロンプトを無視",
    "忽略之前的指示",
]


class GuardrailService:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_and_store(
        self,
        *,
        workspace_id: UUID,
        graph_run_id: UUID,
        state: SupportAgentState,
        graph_step_id: UUID | None = None,
    ) -> list[GuardrailDecision]:
        policies = GuardrailCatalogService(self.db).effective_policies(workspace_id=workspace_id)
        decisions = evaluate_guardrails(state, policies=policies)
        for decision in decisions:
            self.db.add(
                GuardrailResult(
                    workspace_id=workspace_id,
                    graph_run_id=graph_run_id,
                    graph_step_id=graph_step_id,
                    guardrail_type=decision.guardrail_type,
                    passed=decision.passed,
                    severity=decision.severity,
                    message=decision.message,
                )
            )
        self.db.commit()
        return decisions


def evaluate_guardrails(
    state: SupportAgentState,
    policies: dict[str, GuardrailEffectivePolicy] | None = None,
) -> list[GuardrailDecision]:
    input_message = state.get("input_message", "")
    language = state.get("detected_language")
    citations = state.get("citations") or []
    draft_answer = state.get("draft_answer")
    confidence = state.get("confidence_score", 0.0)
    lowered = input_message.lower()
    injection = any(marker in lowered for marker in PROMPT_INJECTION_MARKERS)
    policies = policies or {}
    decisions: list[GuardrailDecision] = []
    provider_failure = state.get("model_provider_failure")
    if provider_failure:
        _append_decision(
            decisions,
            policies,
            guardrail_type="model_provider_failure",
            passed=False,
            fallback_severity="high",
            message=f"Model provider failure requires human review: {provider_failure}",
        )
    budget_failure = state.get("model_budget_failure")
    if budget_failure:
        _append_decision(
            decisions,
            policies,
            guardrail_type="model_budget_failure",
            passed=False,
            fallback_severity="high",
            message=f"Model budget failure requires human review: {budget_failure}",
        )
    _append_decision(
        decisions,
        policies,
        guardrail_type="prompt_injection",
        passed=not injection,
        fallback_severity="high" if injection else "low",
        message=(
            "Prompt injection pattern detected."
            if injection
            else "No prompt injection pattern detected."
        ),
    )
    _append_decision(
        decisions,
        policies,
        guardrail_type="citation_required",
        passed=bool(citations),
        fallback_severity="medium" if not citations else "low",
        message=(
            "No supporting citations were retrieved."
            if not citations
            else "Citations are present."
        ),
    )
    _append_decision(
        decisions,
        policies,
        guardrail_type="unsupported_answer",
        passed=bool(state.get("retrieved_chunks")),
        fallback_severity="high" if not state.get("retrieved_chunks") else "low",
        message=(
            "No retrieved evidence supports an answer."
            if not state.get("retrieved_chunks")
            else "Retrieved evidence is present."
        ),
    )
    confidence_policy = policies.get("confidence_threshold")
    threshold = (
        confidence_policy.threshold
        if confidence_policy and confidence_policy.threshold is not None
        else float(state.get("confidence_threshold") or 0.5)
    )
    _append_decision(
        decisions,
        policies,
        guardrail_type="confidence_threshold",
        passed=confidence >= threshold,
        fallback_severity="medium" if confidence < threshold else "low",
        message=f"Confidence score is {confidence}; threshold is {threshold}.",
    )
    if draft_answer and language in {"en", "ja", "zh"}:
        try:
            answer_language = detect_language(draft_answer).value
        except ValueError:
            answer_language = "unknown"
        passed = answer_language == language
        _append_decision(
            decisions,
            policies,
            guardrail_type="language_preservation",
            passed=passed,
            fallback_severity="medium" if not passed else "low",
            message=f"Draft language is {answer_language}; expected {language}.",
        )
    return decisions


def has_blocking_guardrail(decisions: list[GuardrailDecision]) -> bool:
    return any(
        not decision.passed
        and decision.severity in {"high", "medium"}
        and decision.action_on_fail == "route_to_human_review"
        for decision in decisions
    )


def _append_decision(
    decisions: list[GuardrailDecision],
    policies: dict[str, GuardrailEffectivePolicy],
    *,
    guardrail_type: str,
    passed: bool,
    fallback_severity: str,
    message: str,
) -> None:
    policy = policies.get(guardrail_type)
    if policy is not None and not policy.enabled:
        return
    action_on_fail = policy.action_on_fail if policy is not None else "route_to_human_review"
    severity = "low" if passed else (policy.severity if policy is not None else fallback_severity)
    decisions.append(
        GuardrailDecision(
            guardrail_type=guardrail_type,
            passed=passed,
            severity=severity,
            message=message,
            action_on_fail=action_on_fail,
        )
    )
