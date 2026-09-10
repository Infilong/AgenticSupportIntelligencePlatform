import pytest

from app.modules.support import local_response
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, prepare, run_support


def result_for(decision):
    def inference(request, context):
        source = context["sources"][0]
        return {
            "answer": "Recorded policy response",
            "citations": [{"chunk_id": source["chunk_id"], "quote": source["text"]}]
            if decision in {"answer", "review"}
            else [],
            "review_category": "unclassified",
            "routing": {
                "version": "support-routing-v1",
                "decision": decision,
                "reason": "Test evidence decision",
            },
        }, {"input_tokens": 12}

    return inference


@pytest.mark.parametrize(
    "decision,state,outcome,view",
    [
        ("answer", "completed", "answered", "ready"),
        ("review", "awaiting_review", "policy_review_required", "attention"),
        ("missing", "awaiting_review", "insufficient_evidence", "attention"),
        ("irrelevant", "completed", "set_aside", "all"),
    ],
)
def test_persisted_routes_and_inbox(system, monkeypatch, decision, state, outcome, view):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    monkeypatch.setattr(local_response, "generate", result_for(decision))
    prepare(system)
    run = create(system)
    assert run_support(system)
    client = system["client"]
    detail = client.get(base(system, run)).json()
    assert (detail["state"], detail["outcome"]) == (state, outcome)
    assert detail["review"] is None and detail["reviewed_response"] is None
    assert detail["routing_reason"] == "Test evidence decision"
    path = f"/api/workspaces/{system['workspace']}/messages"
    assert client.get(path, params={"view": view}).json()["total"] == 1
    if decision in {"answer", "irrelevant"}:
        assert client.get(path, params={"view": "attention"}).json()["total"] == 0
        assert not any(step["node"] == "human_review" for step in detail["steps"])
    # Even an admin cannot forge approval for a completed answer or an unsupported draft.
    auth = login(client)
    payload = {
        "action": "approve",
        "reason": "QA",
        "expected_revision": detail["review_version"],
        "draft_hash": detail["draft_hash"],
    }
    if decision != "review":
        assert client.post(base(system, run) + "/review", headers=auth, json=payload).status_code == 409
    if decision == "missing":
        payload["action"] = "clarify"
        payload["response"] = "Which plan do you mean?"
        assert client.post(base(system, run) + "/review", headers=auth, json=payload).status_code == 202
        from tests.integration.review_helpers import run_review

        worked, errors = run_review(system)
        assert worked and not errors
        assert client.get(base(system, run)).json()["outcome"] == "clarification_needed"


def test_meaningless_local_message_needs_no_model_or_review(system, monkeypatch):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    prepare(system)
    run = create(system, original="w")
    assert run_support(system)
    detail = system["client"].get(base(system, run)).json()
    assert (detail["state"], detail["outcome"]) == ("completed", "set_aside")
    assert not detail["model_calls"] and detail["retrieval_id"] is None


@pytest.mark.parametrize("failure", ["cancel", "withdraw"])
def test_automatic_answer_cannot_bypass_publication_fence(system, monkeypatch, failure):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    prepare(system)
    run = create(system)

    def inference(request, context):
        if failure == "cancel":
            auth = login(system["client"])
            assert system["client"].post(base(system, run) + "/cancel", headers=auth).status_code == 200
        else:
            from sqlalchemy import select
            from sqlalchemy.orm import Session

            from app.modules.knowledge.models import Document

            with Session(system["engine"]) as db, db.begin():
                db.scalar(select(Document)).withdrawn = True
        return result_for("answer")(request, context)

    monkeypatch.setattr(local_response, "generate", inference)
    assert run_support(system, expect_failure=True)
    detail = system["client"].get(base(system, run)).json()
    assert detail["outcome"] != "answered" and detail["draft"] is None
