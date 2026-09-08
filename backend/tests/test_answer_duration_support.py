"""Citations cannot justify numeric policy durations absent from their source text."""

import pytest

from app.services.answer_duration_support import has_unverified_durations
from app.services.graph_routing import _route_reasons
from app.services.guardrail_catalog_service import GuardrailEffectivePolicy
from app.services.guardrails import evaluate_guardrails
from app.services.model_provider import MockModelProvider
from tests.test_agents import auth_headers, create_agent, create_workspace, login, register


@pytest.mark.parametrize("language,question,policy,wrong", [
    ("en", "Can I request a refund within 7 days?", "Refunds within 7 days.",
     "Refunds within 700 days."),
    ("ja", "7日以内に返金できますか？", "返金は7日以内です。", "返金は700日以内です。"),
    ("zh", "7天内可以退款吗？", "退款期限为7天。", "退款期限为700天。"),
])
def test_invented_cited_duration_requires_review(
    client, monkeypatch, language, question, policy, wrong,
):
    register(client, "duration-owner@example.test")
    token = login(client, "duration-owner@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}"
    uploaded = client.post(base + "/knowledge-documents", headers=headers, json={
        "title": "Policy", "language": language, "content_type": "text/plain",
        "content": question + "\n" + policy,
    })
    assert uploaded.status_code == 201
    agent = create_agent(client, token, workspace["id"])
    original = MockModelProvider.complete

    def invented(self, **kwargs):
        if kwargs["purpose"] == "draft_response":
            kwargs["completion_text"] = wrong + "\n" + kwargs["completion_text"].rsplit("\n", 1)[-1]
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", invented)
    response = client.post(base + f"/agents/{agent['id']}/runs", headers=headers,
                           json={"input_message": question, "language": language})
    assert response.status_code == 201
    run = response.json()
    assert run["status"] == "needs_human_review"
    assert run["final_answer"] is None
    trace = client.get(base + f"/agent-runs/{run['id']}/trace", headers=headers).json()
    assert len(trace["ai_runs"]) == 2
    assert all(call["status"] == "succeeded" and call["total_tokens"] > 0
               for call in trace["ai_runs"])
    assert any(row["guardrail_type"] == "citation_required" and row["passed"]
               for row in trace["guardrails"])
    assert any(row["guardrail_type"] == "unsupported_answer" and not row["passed"]
               for row in trace["guardrails"])
    assert not any(step["step_name"] == "finalize_response" for step in trace["steps"])
    review = client.get(base + "/human-reviews", headers=headers).json()["items"][0]
    assert "unsupported_answer" in review["reason"]
    assert wrong in review["proposed_answer"]


@pytest.mark.parametrize("answer,source,passed", [
    ("Refunds within 700 days.", "Refunds within 7 days.", False),
    ("返金は７００日以内です。", "返金は7日以内です。", False),
    ("退款期限为700天。", "退款期限为7天。", False),
    ("Refunds within 7 days.", "Refunds within 7 days.", True),
    ("返金は７日以内です。", "返金は7日以内です。", True),
    ("Refunds take 7 business days.", "Refunds take 7 days.", False),
])
def test_unsupported_guard_compares_durations(answer, source, passed):
    state = {"draft_answer": answer + "\nPolicy v1 #chunk-0 (source)",
             "retrieved_chunks": [{"content": source}],
             "packed_context_chunks": [{"content": source,
                                        "citation": "Policy v1 #chunk-0 (source)"}]}
    decision = next(item for item in evaluate_guardrails(state)
                    if item.guardrail_type == "unsupported_answer")
    assert decision.passed is passed


@pytest.mark.parametrize("answer,source,missing", [
    ("A 700-day window.", "A 7-day window.", True),
    ("A 7-day window.", "Within 7 days.", False),
    ("Wait 1.5 hours.", "Wait 1.50 hours.", False),
    ("Wait 15 hours.", "Wait 1.5 hours.", True),
    ("Wait 1,000 days.", "Wait 1000 days.", False),
    ("Wait 1 hour.", "Wait 60 minutes.", True),
    ("7 営業日以内です。", "7日以内です。", True),
    ("需要7个工作日。", "需要7天。", True),
    ("退款需要7天。", "Refunds take 7 days.", False),
    ("Supported prose without quantities.", "Some source text.", False),
])
def test_duration_normalization_is_conservative(answer, source, missing):
    assert has_unverified_durations({
        "draft_answer": answer + "\nPolicy v1 #chunk-0 (source)",
        "packed_context_chunks": [{"citation": "Policy v1 #chunk-0 (source)", "content": source}],
    }) is missing


def test_uncited_chunks_and_citation_metadata_do_not_support_invented_duration():
    state = {"draft_answer": "Refunds within 700 days.\n700 days v1 #chunk-0 (source)",
             "packed_context_chunks": [
                 {"citation": "700 days v1 #chunk-0 (source)", "content": "Refunds within 7 days."},
                 {"citation": "Other v1 #chunk-1 (other)", "content": "Retention is 700 days."},
             ]}
    assert has_unverified_durations(state)
    state["draft_answer"] = "Refunds within 7 days.\n700 days v1 #chunk-0 (source)"
    assert not has_unverified_durations(state)


@pytest.mark.parametrize("enabled,action,routes", [
    (True, "route_to_human_review", True), (False, "route_to_human_review", False),
    (True, "log_only", False),
])
def test_duration_check_preserves_guardrail_policy_actions(enabled, action, routes):
    state = {"draft_answer": "700 days.\nPolicy", "confidence_score": 1,
             "retrieved_chunks": [{"content": "7 days."}],
             "packed_context_chunks": [{"content": "7 days.", "citation": "Policy"}]}
    policy = GuardrailEffectivePolicy("unsupported_answer", enabled, "high", action, None)
    reasons = _route_reasons(state, 0.5, {"unsupported_answer": policy})
    assert ("unsupported_answer" in reasons) is routes
