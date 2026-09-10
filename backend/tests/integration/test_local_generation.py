import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.support import local_response
from app.modules.support.models import Handoff
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, prepare, run_support


def inference(request, context):
    source = context["sources"][0]
    return {
        "answer": "Source-backed automatic draft",
        "review_category": "unclassified",
        "citations": [{"chunk_id": source["chunk_id"], "quote": source["text"]}],
    }, {"input_tokens": 12}


def test_local_graph_draft_and_admin_review(system, monkeypatch):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    monkeypatch.setattr(local_response, "generate", inference)
    prepare(system)
    run = create(system)
    assert run_support(system)
    client = system["client"]
    detail = client.get(base(system, run)).json()
    assert detail["state"] == "awaiting_review", detail
    assert detail["draft"] == "Source-backed automatic draft"
    assert detail["handoff"]["provider"] == "local_ollama"
    assert detail["handoff"]["contributor_id"] is None
    call = next(call for call in detail["model_calls"] if call["operation"] == "generate")
    assert call["input_tokens"] == 12 and call["status"] == "succeeded"
    with Session(system["engine"]) as db:
        handoff = db.scalar(select(Handoff))
        assert local_response.snapshot(db, handoff)["answer"] == detail["draft"]
    auth = login(client, "operator")
    payload = {
        "action": "approve",
        "reason": "Checked policy",
        "expected_revision": detail["review_version"],
        "draft_hash": detail["draft_hash"],
    }
    url = base(system, run) + "/review"
    assert client.post(url, headers=auth, json=payload).status_code == 403
    auth = login(client)
    assert client.post(url, headers=auth, json=payload).status_code == 202
    from tests.integration.review_helpers import run_review

    worked, errors = run_review(system)
    assert worked and not errors, errors
    assert client.get(base(system, run)).json()["outcome"] == "approved_response"


@pytest.mark.parametrize("problem", ["failure", "stale", "cancelled", "uncertain", "uncertain_failure"])
def test_local_generation_failures_do_not_publish(system, monkeypatch, problem):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    prepare(system)
    run = create(system)

    def broken(request, context):
        if problem == "failure":
            raise TimeoutError("Synthetic local timeout")
        if problem == "cancelled":
            auth = login(system["client"])
            assert system["client"].post(base(system, run) + "/cancel", headers=auth).status_code == 200
        elif problem.startswith("uncertain"):
            from app.modules.usage.models import ModelCall

            with Session(system["engine"]) as db, db.begin():
                call = db.scalar(select(ModelCall).where(ModelCall.operation == "generate"))
                call.status = "uncertain"
            if problem == "uncertain_failure":
                raise TimeoutError("Late timeout after reconciliation")
        else:
            from app.modules.knowledge.models import Document

            with Session(system["engine"]) as db, db.begin():
                document = db.scalar(select(Document))
                document.withdrawn = True
        return inference(request, context)

    monkeypatch.setattr(local_response, "generate", broken)
    assert run_support(system, expect_failure=True)
    detail = system["client"].get(base(system, run)).json()
    assert detail["draft"] is None and detail["state"] != "awaiting_review"
    if problem.startswith("uncertain"):
        assert next(c for c in detail["model_calls"] if c["operation"] == "generate")["status"] == "uncertain"


def test_existing_manual_handoff_stays_manual(system, monkeypatch):
    from tests.integration.support_helpers import draft_payload

    prepare(system)
    run = create(system)
    assert run_support(system)
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    client = system["client"]
    auth = login(client)
    path = base(system, run)
    handoff = client.get(path + "/development-handoff").json()
    assert (
        client.post(
            path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff)
        ).status_code
        == 202
    )
    assert run_support(system)
    result = client.get(path).json()
    assert result["state"] == "awaiting_review"
    assert result["handoff"]["provider"] == "codex_assisted_development"
    assert not any(c["operation"] == "generate" for c in result["model_calls"])


def test_frozen_comparison_stays_manual(system, monkeypatch):
    from tests.integration.test_generation_comparisons import create as compare
    from tests.integration.test_generation_comparisons import work

    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    prepare(system)
    path, _ = compare(system)
    work(system)
    with Session(system["engine"]) as db:
        handoff = db.scalar(select(Handoff))
        assert handoff.provider == "codex_assisted_development"
        assert handoff.response is None


def test_local_model_can_report_insufficient_evidence(system, monkeypatch):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    monkeypatch.setattr(
        local_response,
        "generate",
        lambda request, context: (
            {
                "answer": "Please specify which policy you need.",
                "citations": [],
                "review_category": "unclassified",
            },
            {"input_tokens": 10},
        ),
    )
    prepare(system)
    run = create(system)
    assert run_support(system)
    result = system["client"].get(base(system, run)).json()
    assert result["state"] == "awaiting_review" and result["outcome"] == "insufficient_evidence"
    assert result["draft_hash"] and "routing decision" in result["routing_reason"]
    assert result["draft"] == "Please specify which policy you need."
    assert result["citations"] == [] and result["reviewed_response"] is None
