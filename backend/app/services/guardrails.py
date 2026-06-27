from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import detect_language
from app.models.review import GuardrailResult
from app.services.support_agent_state import SupportAgentState


@dataclass(frozen=True)
class GuardrailDecision:
    guardrail_type: str
    passed: bool
    severity: str
    message: str


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
    ) -> list[GuardrailDecision]:
        decisions = evaluate_guardrails(state)
        for decision in decisions:
            self.db.add(
                GuardrailResult(
                    workspace_id=workspace_id,
                    graph_run_id=graph_run_id,
                    graph_step_id=None,
                    guardrail_type=decision.guardrail_type,
                    passed=decision.passed,
                    severity=decision.severity,
                    message=decision.message,
                )
            )
        self.db.commit()
        return decisions


def evaluate_guardrails(state: SupportAgentState) -> list[GuardrailDecision]:
    input_message = state.get("input_message", "")
    language = state.get("detected_language")
    citations = state.get("citations") or []
    draft_answer = state.get("draft_answer")
    confidence = state.get("confidence_score", 0.0)
    lowered = input_message.lower()
    injection = any(marker in lowered for marker in PROMPT_INJECTION_MARKERS)
    decisions = []
    provider_failure = state.get("model_provider_failure")
    if provider_failure:
        decisions.append(
            GuardrailDecision(
                "model_provider_failure",
                False,
                "high",
                f"Model provider failure requires human review: {provider_failure}",
            )
        )
    decisions.extend([
        GuardrailDecision(
            "prompt_injection",
            not injection,
            "high" if injection else "low",
            (
                "Prompt injection pattern detected."
                if injection
                else "No prompt injection pattern detected."
            ),
        ),
        GuardrailDecision(
            "citation_required",
            bool(citations),
            "medium" if not citations else "low",
            (
                "No supporting citations were retrieved."
                if not citations
                else "Citations are present."
            ),
        ),
        GuardrailDecision(
            "unsupported_answer",
            bool(state.get("retrieved_chunks")),
            "high" if not state.get("retrieved_chunks") else "low",
            (
                "No retrieved evidence supports an answer."
                if not state.get("retrieved_chunks")
                else "Retrieved evidence is present."
            ),
        ),
        GuardrailDecision(
            "confidence_threshold",
            confidence >= 0.5,
            "medium" if confidence < 0.5 else "low",
            f"Confidence score is {confidence}.",
        ),
    ])
    if draft_answer and language in {"en", "ja", "zh"}:
        try:
            answer_language = detect_language(draft_answer).value
        except ValueError:
            answer_language = "unknown"
        passed = answer_language == language
        decisions.append(
            GuardrailDecision(
                "language_preservation",
                passed,
                "medium" if not passed else "low",
                f"Draft language is {answer_language}; expected {language}.",
            )
        )
    return decisions


def has_blocking_guardrail(decisions: list[GuardrailDecision]) -> bool:
    return any(
        not decision.passed and decision.severity in {"high", "medium"}
        for decision in decisions
    )
