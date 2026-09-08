"""Compare persisted metrics only under a known matching evaluation contract."""

import json
from collections import Counter

from app.models.evaluation import EvaluationRun
from app.services.evaluation_scoring import EVALUATION_CONTRACT

LOWER_IS_BETTER_METRICS = {
    "average_latency_ms",
    "average_prompt_tokens",
    "estimated_cost_per_run",
}
METRIC_DELTA_TOLERANCE = 0.000001


def _contract_matches(current_run, baseline_run, mode, language):
    def identities(run):
        scores = [json.loads(result.scores_json) for result in run.results
                  if str(result.mode) == mode and str(result.language) == language]
        if not scores or any(score.get("evaluation_contract") != EVALUATION_CONTRACT
                             for score in scores):
            return None
        hashes = [score.get("evaluation_case_fingerprint") for score in scores]
        if any(not isinstance(value, str) or len(value) != 64 or
               any(char not in "0123456789abcdef" for char in value) for value in hashes):
            return None
        return Counter(hashes)
    current = identities(current_run)
    return current is not None and current == identities(baseline_run)


def compare_metrics(
    current_run: EvaluationRun, baseline_run: EvaluationRun,
) -> list[dict[str, object]]:
    current_metrics = {
        (str(metric.mode), str(metric.language), metric.metric_name): metric.metric_value
        for metric in current_run.metrics
    }
    baseline_metrics = {
        (str(metric.mode), str(metric.language), metric.metric_name): metric.metric_value
        for metric in baseline_run.metrics
    }
    keys = sorted(
        set(current_metrics) | set(baseline_metrics),
        key=lambda item: (item[0], item[1], _metric_sort_key(item[2])),
    )
    deltas: list[dict[str, object]] = []
    for mode, language, metric_name in keys:
        current_value = current_metrics.get((mode, language, metric_name))
        baseline_value = baseline_metrics.get((mode, language, metric_name))
        compatible = _contract_matches(current_run, baseline_run, mode, language)
        delta = (
            current_value - baseline_value
            if compatible and current_value is not None and baseline_value is not None
            else None
        )
        deltas.append(
            {
                "mode": mode,
                "language": language,
                "metric_name": metric_name,
                "current_value": current_value,
                "baseline_value": baseline_value,
                "delta": delta,
                "direction": (_metric_direction(metric_name, current_value, baseline_value)
                              if compatible else "incomparable"),
            }
        )
    return deltas


def _metric_sort_key(metric_name: str) -> tuple[int, str]:
    order = [
        "case_pass_rate",
        "human_review_routing_accuracy",
        "tool_call_correctness",
        "guardrail_failure_detection_rate",
        "citation_presence_rate",
        "citation_accuracy",
        "language_preservation_pass_rate",
        "average_prompt_tokens",
        "estimated_cost_per_run",
        "average_latency_ms",
    ]
    try:
        return order.index(metric_name), metric_name
    except ValueError:
        return len(order), metric_name


def _metric_direction(
    metric_name: str, current_value: float | None, baseline_value: float | None
) -> str:
    if current_value is None:
        return "missing"
    if baseline_value is None:
        return "new"
    delta = current_value - baseline_value
    if abs(delta) <= METRIC_DELTA_TOLERANCE:
        return "unchanged"
    if metric_name in LOWER_IS_BETTER_METRICS:
        return "improved" if delta < 0 else "regressed"
    return "improved" if delta > 0 else "regressed"
