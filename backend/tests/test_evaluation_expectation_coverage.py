import json
from types import SimpleNamespace

import pytest

from app.core.language import SupportedLanguage
from app.services.evaluation_loader import LoadedEvaluationCase
from app.services.evaluation_metrics import calculate_metrics
from app.services.evaluation_runner import _score_case
from tests.test_agents import auth_headers, create_workspace, login, register


def result(*, expected_tools=(), expected_guardrails=(), actual_tools=(), actual_guardrails=(),
           mode="system_v1", language="en"):
    case = LoadedEvaluationCase("case", SupportedLanguage(language), "Question",
                                expected_tool_calls=list(expected_tools),
                                expected_guardrail_failures=list(expected_guardrails))
    scores = _score_case(loaded_case=case, actual_route="finalize", answer="Policy",
                         citations=["Policy"], actual_tool_calls=list(actual_tools),
                         actual_guardrail_failures=list(actual_guardrails))
    return SimpleNamespace(mode=mode, language=language, passed=True,
                           scores_json=json.dumps(scores), citations_json='["Policy"]',
                           latency_ms=1, prompt_tokens=1, estimated_cost=0)


def test_untested_behaviors_do_not_emit_quality_rates():
    item = result()
    scores = json.loads(item.scores_json)
    assert scores["tool_call_match"] is None
    assert scores["guardrail_failure_match"] is None
    metrics = calculate_metrics([item])[("system_v1", "en")]
    for key in ("tool_call_correctness", "guardrail_failure_detection_rate",
                "expected_tool_call_match_rate", "expected_guardrail_detection_rate"):
        assert key not in metrics


@pytest.mark.parametrize("expectation,key", [
    ({"expected_tools": ["search_documents"]}, "expected_tool_call_match_rate"),
    ({"expected_guardrails": ["prompt_injection"]}, "expected_guardrail_detection_rate"),
])
def test_untested_cases_cannot_mask_a_failed_expectation(expectation, key):
    metrics = calculate_metrics([result(**expectation)] + [result() for _ in range(9)])
    assert metrics[("system_v1", "en")][key] == 0


def test_expected_lists_are_persisted_and_grouping_stays_independent():
    failed = result(expected_tools=["search_documents"])
    success = result(expected_tools=["search_documents"], actual_tools=["search_documents"])
    japanese = result(language="ja")
    baseline = result(mode="direct_llm")
    scores = json.loads(failed.scores_json)
    assert scores["expected_tool_calls"] == ["search_documents"]
    assert scores["expected_guardrail_failures"] == []
    metrics = calculate_metrics([failed, success, japanese, baseline])
    assert metrics[("system_v1", "en")]["expected_tool_call_match_rate"] == 0.5
    assert "expected_tool_call_match_rate" not in metrics[("system_v1", "ja")]
    assert "expected_tool_call_match_rate" not in metrics[("direct_llm", "en")]


def test_legacy_scores_without_expectations_cannot_prove_coverage():
    item = result()
    item.scores_json = json.dumps({"tool_call_match": 1.0, "guardrail_failure_match": 1.0})
    metrics = calculate_metrics([item])[("system_v1", "en")]
    assert "expected_tool_call_match_rate" not in metrics
    assert "expected_guardrail_detection_rate" not in metrics


@pytest.mark.parametrize("tested", [False, True])
def test_api_preserves_expectation_provenance_and_only_emits_measured_rates(client, tested):
    register(client, "coverage@example.test")
    token = login(client, "coverage@example.test")
    workspace = create_workspace(client, token)
    case = {"id": "coverage", "language": "en", "input_message": "Refund policy?"}
    if tested:
        case.update(expected_tool_calls=["search_documents"],
                    expected_guardrail_failures=["prompt_injection"])
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                           headers=auth_headers(token), json={
        "name": "Coverage", "modes": ["direct_llm"], "jsonl_cases": json.dumps(case),
    })
    assert response.status_code == 201
    body = response.json()
    scores = json.loads(body["results"][0]["scores_json"])
    assert scores["expected_tool_calls"] == case.get("expected_tool_calls", [])
    assert scores["expected_guardrail_failures"] == case.get("expected_guardrail_failures", [])
    metrics = {row["metric_name"]: row["metric_value"] for row in body["metrics"]}
    for key in ("expected_tool_call_match_rate", "expected_guardrail_detection_rate"):
        if tested:
            assert metrics[key] == 0
        else:
            assert key not in metrics
    assert "tool_call_correctness" not in metrics
    assert "guardrail_failure_detection_rate" not in metrics
