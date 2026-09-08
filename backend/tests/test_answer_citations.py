import pytest

from app.services.answer_citations import has_answer_citations
from app.services.guardrails import evaluate_guardrails
from app.services.model_provider import MockModelProvider
from tests.test_agents import auth_headers, create_agent, create_workspace, login, register


@pytest.mark.parametrize("suffix,expected", [
    ("", True),
    ("\nPolicy v1 #chunk-0 (known)", True),
    ("\nOther v1 #chunk-1 (unknown)", False),
    ("\nPolicy v2 #chunk-0 (known)", False),
    ("\nPolicy v1 #chunk-99 (known)", False),
    ("\nPolicy v1 #chunk-broken", False),
])
def test_valid_citation_does_not_mask_additional_invalid_chunk_reference(suffix, expected):
    citation = "Policy v1 #chunk-0 (known)"
    assert has_answer_citations({
        "draft_answer": citation + suffix,
        "packed_context_chunks": [{"content": "Seven-day refund policy", "citation": citation}],
    }) is expected


@pytest.mark.parametrize("packed,expected", [
    ([{"content": "Policy text", "citation": "Exact source"}], True),
    ([], False),
    ([{"content": "Policy text", "citation": "Different source"}], False),
    ([{"content": "", "citation": "Exact source"}], False),
])
def test_only_nonempty_packed_sources_can_supply_answer_citations(packed, expected):
    assert has_answer_citations({
        "draft_answer": "Supported response. Exact source", "packed_context_chunks": packed,
        "citations": ["Exact source"],
        "retrieved_chunks": [{"content": "Policy text", "citation": "Exact source"}],
    }) is expected


@pytest.mark.parametrize("answer", ["Refunds within 7 days.", "", "[Invented policy]"])
def test_retrieval_metadata_cannot_satisfy_answer_citation(answer):
    state = {"input_message": "Refund?", "detected_language": "en", "draft_answer": answer,
             "citations": ["Policy v1 #chunk-0 (source-id)"],
             "retrieved_chunks": [{"content": "Refunds within 7 days."}],
             "packed_context_chunks": [{"content": "Refunds within 7 days.",
                                        "citation": "Policy v1 #chunk-0 (source-id)"}],
             "confidence_score": 0.99}
    citation = next(item for item in evaluate_guardrails(state)
                    if item.guardrail_type == "citation_required")
    assert not citation.passed


@pytest.mark.parametrize("language,question,policy", [
    ("en", "Can I request a refund within 7 days?", "Refunds within 7 days."),
    ("ja", "7日以内に返金できますか？", "返金は7日以内です。"),
    ("zh", "7天内可以退款吗？", "退款期限为7天。"),
])
@pytest.mark.parametrize("citation_mode", ["missing", "mixed"])
def test_uncited_provider_answer_routes_to_review_with_ledger_and_trace(
    client, monkeypatch, language, question, policy, citation_mode,
):
    register(client, "citation-owner@example.test")
    token = login(client, "citation-owner@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}"
    upload = client.post(f"{base}/knowledge-documents", headers=headers,
                         json={"title": "Policy", "language": language,
                               "content_type": "text/plain", "content": question + "\n" + policy})
    assert upload.status_code == 201
    agent = create_agent(client, token, workspace["id"])
    original = MockModelProvider.complete
    proposed = []

    def uncited(self, **kwargs):
        if kwargs["purpose"] == "draft_response":
            kwargs["completion_text"] = (policy if citation_mode == "missing" else
                policy + "\n" + kwargs["completion_text"].rsplit("\n", 1)[-1]
                + "\nInvented v1 #chunk-99 (unknown)")
            proposed.append(kwargs["completion_text"])
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", uncited)
    result = client.post(f"{base}/agents/{agent['id']}/runs", headers=headers,
                         json={"input_message": question})
    assert result.status_code == 201
    run = result.json()
    assert run["status"] == "needs_human_review"
    assert run["final_answer"] is None
    trace = client.get(f"{base}/agent-runs/{run['id']}/trace", headers=headers).json()
    assert len(trace["ai_runs"]) == 2
    assert all(call["total_tokens"] > 0 for call in trace["ai_runs"])
    assert all(call["status"] == "succeeded" for call in trace["ai_runs"])
    assert any(row["guardrail_type"] == "citation_required" and not row["passed"]
               for row in trace["guardrails"])
    assert not any(step["step_name"] == "finalize_response" for step in trace["steps"])
    review = client.get(f"{base}/human-reviews", headers=headers).json()["items"][0]
    assert "citation_required" in review["reason"]
    assert review["proposed_answer"] == proposed[0]
