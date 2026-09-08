"""Deterministic graph routing rules honoring workspace guardrail policies."""

from app.services.answer_citations import has_answer_citations
from app.services.answer_duration_support import has_unverified_durations
from app.services.guardrail_catalog_service import GuardrailEffectivePolicy
from app.services.support_agent_state import SupportAgentState


def _route_reasons(
    state: SupportAgentState,
    confidence_threshold: float,
    policies: dict[str, GuardrailEffectivePolicy],
) -> list[str]:
    checks = {
        "model_provider_failure": bool(state.get("model_provider_failure")),
        "model_budget_failure": bool(state.get("model_budget_failure")),
        "unsafe_tool_call": bool(state.get("tool_disabled")),
        "confidence_threshold": state.get("confidence_score", 0) < confidence_threshold,
        "prompt_injection": state.get("intent") == "prompt_injection",
        "privacy_complaint": state.get("intent") == "privacy_complaint",
        "high_safety_risk": state.get("safety_risk") == "high",
        "escalation_needed": bool(state.get("escalation_needed")),
        "citation_required": not has_answer_citations(state),
        "unsupported_answer": bool(state.get("no_source")) or has_unverified_durations(state),
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
