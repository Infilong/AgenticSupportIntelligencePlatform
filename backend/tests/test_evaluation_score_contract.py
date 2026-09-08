import json
from types import SimpleNamespace

from app.core.language import SupportedLanguage
from app.services.evaluation_loader import LoadedEvaluationCase
from app.services.evaluation_metrics import calculate_metrics
from app.services.evaluation_runner import _score_case


def score(case, answer, citations, route="finalize"):
    return _score_case(loaded_case=case, actual_route=route, answer=answer, citations=citations,
                       actual_tool_calls=[], actual_guardrail_failures=[])


def test_citations_do_not_establish_factual_groundedness():
    case = LoadedEvaluationCase("policy", SupportedLanguage.en, "Refund?",
                                must_include=["7 days"], must_not_include=["30 days"])
    scores = score(case, "Refunds are allowed for 30 days. [Policy]", ["Policy"])
    assert "groundedness" not in scores
    assert scores["must_include"] == 0
    assert scores["must_not_include"] == 0


def test_all_expected_sources_are_required():
    case = LoadedEvaluationCase("sources", SupportedLanguage.en, "Policy?",
                                expected_sources=["Refund Policy", "Regional Exception"])
    assert score(case, "Policy details", ["Refund Policy v1"])["citation_accuracy"] == 0
    assert score(case, "Policy details", ["Refund Policy v1", "Regional Exception v2"])[
        "citation_accuracy"] == 1


def test_review_pass_does_not_inflate_citation_presence():
    case = LoadedEvaluationCase("review", SupportedLanguage.en, "Unknown policy?",
                                expected_route="human_review")
    scores = score(case, None, [], route="human_review")
    assert all(value == 1 for value in scores.values() if isinstance(value, float))
    item = SimpleNamespace(mode="system_v1", language="en", passed=True,
                           scores_json=json.dumps(scores), citations_json="[]", latency_ms=1,
                           prompt_tokens=0, estimated_cost=0)
    metrics = calculate_metrics([item])[("system_v1", "en")]
    assert metrics["case_pass_rate"] == 1
    assert metrics["citation_presence_rate"] == 0
    assert "groundedness_pass_rate" not in metrics
