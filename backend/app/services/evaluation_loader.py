from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.core.language import SupportedLanguage


class EvaluationCaseLoadError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedEvaluationCase:
    external_id: str
    language: SupportedLanguage
    input_message: str
    expected_intent: str | None = None
    expected_sources: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)
    must_not_include: list[str] = field(default_factory=list)
    expected_route: str = "finalize"
    safety_risk: str = "low"
    max_prompt_tokens: int | None = None
    expected_tool_calls: list[str] = field(default_factory=list)
    expected_guardrail_failures: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


def load_jsonl_cases(content: str) -> list[LoadedEvaluationCase]:
    cases: list[LoadedEvaluationCase] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise EvaluationCaseLoadError(f"Invalid JSONL at line {line_number}.") from exc
        try:
            external_id = str(raw["id"]).strip()
            language = SupportedLanguage(raw["language"])
            input_message = str(raw["input_message"]).strip()
        except (KeyError, ValueError) as exc:
            raise EvaluationCaseLoadError(
                f"Invalid evaluation case at line {line_number}."
            ) from exc
        if not external_id or not input_message:
            raise EvaluationCaseLoadError(f"Blank evaluation case field at line {line_number}.")
        cases.append(
            LoadedEvaluationCase(
                external_id=external_id,
                language=language,
                input_message=input_message,
                expected_intent=raw.get("expected_intent"),
                expected_sources=list(raw.get("expected_sources", [])),
                must_include=list(raw.get("must_include", [])),
                must_not_include=list(raw.get("must_not_include", [])),
                expected_route=str(raw.get("expected_route", "finalize")),
                safety_risk=str(raw.get("safety_risk", "low")),
                max_prompt_tokens=raw.get("max_prompt_tokens"),
                expected_tool_calls=list(raw.get("expected_tool_calls", [])),
                expected_guardrail_failures=list(raw.get("expected_guardrail_failures", [])),
                metadata=dict(raw.get("metadata", {})),
            )
        )
    if not cases:
        raise EvaluationCaseLoadError("Evaluation JSONL did not contain any cases.")
    return cases
