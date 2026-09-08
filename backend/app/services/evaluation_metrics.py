from __future__ import annotations

import json
from collections import defaultdict

from app.models.evaluation import EvaluationResult


def calculate_metrics(results: list[EvaluationResult]) -> dict[tuple[str, str], dict[str, float]]:
    grouped: dict[tuple[str, str], list[EvaluationResult]] = defaultdict(list)
    for result in results:
        grouped[(str(result.mode), str(result.language))].append(result)

    metrics: dict[tuple[str, str], dict[str, float]] = {}
    for key, items in grouped.items():
        total = len(items)
        if total == 0:
            continue
        decoded_scores = [json.loads(item.scores_json) for item in items]
        metrics[key] = {
            "case_pass_rate": _ratio(item.passed for item in items),
            "human_review_routing_accuracy": _average(
                score.get("route_match", 0.0) for score in decoded_scores
            ),
            "language_preservation_pass_rate": _average(
                score.get("language_preserved", 0.0) for score in decoded_scores
            ),
            "citation_accuracy": _average(
                score.get("citation_accuracy", 0.0) for score in decoded_scores
            ),
            "citation_presence_rate": _ratio(
                bool(json.loads(item.citations_json)) for item in items
            ),
            "average_latency_ms": _average(item.latency_ms for item in items),
            "average_prompt_tokens": _average(item.prompt_tokens for item in items),
            "estimated_cost_per_run": _average(item.estimated_cost for item in items),
        }
        for name, expectation, score_name in (
            ("expected_tool_call_match_rate", "expected_tool_calls", "tool_call_match"),
            ("expected_guardrail_detection_rate", "expected_guardrail_failures",
             "guardrail_failure_match"),
        ):
            evaluated = [score[score_name] for score in decoded_scores
                         if isinstance(score.get(expectation), list) and score[expectation]
                         and score_name in score]
            if evaluated:
                metrics[key][name] = _average(evaluated)
    return metrics


def _ratio(values) -> float:
    items = list(values)
    return round(sum(1 for item in items if item) / len(items), 4) if items else 0.0


def _average(values) -> float:
    items = [float(value) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0
