"""Per-case acceptance checks with explicit optional expectation provenance."""

from app.core.answer_language import detect_answer_language
from app.services.evaluation_case_identity import case_fingerprint
from app.services.evaluation_loader import LoadedEvaluationCase

EVALUATION_CONTRACT = "2026-09-08-case-identity-v2"


def _score_case(
    *,
    loaded_case: LoadedEvaluationCase,
    actual_route: str,
    answer: str | None,
    citations: list[str],
    actual_tool_calls: list[str],
    actual_guardrail_failures: list[str],
    prompt_tokens: int | None = None,
) -> dict[str, float | str | list[str] | None]:
    answer_text = answer or ""
    route_match = 1.0 if actual_route == loaded_case.expected_route else 0.0
    must_include = 1.0 if all(item in answer_text for item in loaded_case.must_include) else 0.0
    must_not_include = (
        1.0 if all(item not in answer_text for item in loaded_case.must_not_include) else 0.0
    )
    citation_accuracy = 1.0
    if loaded_case.expected_sources:
        citation_accuracy = (
            1.0
            if all(any(expected in citation for citation in citations)
                   for expected in loaded_case.expected_sources)
            else 0.0
        )
    elif loaded_case.expected_route == "finalize":
        citation_accuracy = 1.0 if citations else 0.0
    language_preserved = _language_preserved(answer_text, loaded_case.language, citations)
    tool_call_match = _expected_subset_score(loaded_case.expected_tool_calls, actual_tool_calls)
    guardrail_failure_match = _expected_subset_score(
        loaded_case.expected_guardrail_failures, actual_guardrail_failures
    )
    return {
        "evaluation_contract": EVALUATION_CONTRACT,
        "evaluation_case_fingerprint": case_fingerprint(loaded_case),
        "prompt_token_limit_match": (
            None if loaded_case.max_prompt_tokens is None else
            float(prompt_tokens is not None and prompt_tokens <= loaded_case.max_prompt_tokens)
        ),
        "route_match": route_match,
        "must_include": must_include,
        "must_not_include": must_not_include,
        "citation_accuracy": citation_accuracy,
        "language_preserved": language_preserved,
        "tool_call_match": tool_call_match,
        "guardrail_failure_match": guardrail_failure_match,
        "expected_tool_calls": list(loaded_case.expected_tool_calls),
        "expected_guardrail_failures": list(loaded_case.expected_guardrail_failures),
        "actual_tool_calls": actual_tool_calls,
        "actual_guardrail_failures": actual_guardrail_failures,
    }


def _expected_subset_score(expected: list[str], actual: list[str]) -> float | None:
    if not expected:
        return None
    actual_set = set(actual)
    return 1.0 if all(item in actual_set for item in expected) else 0.0


def _language_preserved(answer: str, language, citations=()) -> float:
    if not answer:
        return 1.0
    try:
        return 1.0 if detect_answer_language(answer, citations) == language else 0.0
    except ValueError:
        return 0.0


