import uuid
from datetime import datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.models import Handoff, Message, SupportRun
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, draft_payload, prepare, run_support


@pytest.mark.parametrize(
    "original,language,answer",
    [
        ("What is the refund deadline?", "en", "The refund deadline is fourteen days."),
        ("返金の申請期限はいつですか？", "ja", "返金の申請期限は14日以内です。"),
        ("退款申请的截止日期是什么？", "zh", "退款申请的截止日期是十四天。"),
    ],
)
def test_real_graph_retrieval_handoff_and_cited_draft(system, original, language, answer):
    prepare(system)
    run = create(system, original, language)
    assert run_support(system)
    client = system["client"]
    path = base(system, run)
    waiting = client.get(path).json()
    assert waiting["state"] == "waiting_for_input", waiting
    assert waiting["original"] == original
    assert waiting["model_calls"] and waiting["retrieval_id"]
    assert client.get(path + "/development-handoff").status_code == 403
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    assert handoff["context"]["original"] == original
    submitted = client.post(
        path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff, answer)
    )
    assert submitted.status_code == 202, submitted.text
    # New graph and database connection resume the saved interrupt.
    assert run_support(system), system.get("claim_diagnostic")
    result = client.get(path).json()
    assert result["state"] == "awaiting_review", result
    assert result["outcome"] == "grounded_draft" and result["reviewed_response"] is None
    assert result["draft"] == answer
    assert result["citations"][0]["quote"] in handoff["context"]["sources"][0]["text"]
    assert result["support_status"] == "not_verified"
    assert result["handoff"]["provider"] == "codex_assisted_development"
    timing = result["handoff"]
    delta = (
        datetime.fromisoformat(timing["submitted_at"]) - datetime.fromisoformat(timing["created_at"])
    ).total_seconds() * 1000
    assert timing["timing_status"] == ("clock_anomaly" if delta < 0 else "recorded")
    assert timing["handoff_elapsed_ms"] == (None if delta < 0 else delta)
    assert {s["node"] for s in result["steps"]} == {
        "validate_input",
        "retrieve_evidence",
        "development_generation",
        "human_review",
    }
    assert all(call["api_cost_usd"] == 0 for call in result["model_calls"])


def test_message_atomic_idempotency_and_permissions(system):
    run = create(system)
    assert create(system) == run
    client, ws = system["client"], system["workspace"]
    auth = login(client, "operator")
    assert (
        client.post(
            f"/api/workspaces/{ws}/messages",
            headers={**auth, "Idempotency-Key": "message-1"},
            json={"original": "different", "language": "en"},
        ).status_code
        == 409
    )
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Message)) == 1
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 1
        assert db.scalar(select(func.count()).select_from(Job)) == 1
    viewer = login(client, "viewer")
    assert client.get(base(system, run)).status_code == 200
    assert (
        client.post(
            f"/api/workspaces/{ws}/messages",
            headers={**viewer, "Idempotency-Key": "viewer"},
            json={"original": "A question", "language": "en"},
        ).status_code
        == 403
    )
    login(client, "other")
    assert client.get(base(system, run)).status_code == 404
    assert client.get(f"/api/workspaces/{ws}/messages").status_code == 404


def test_meaningless_input_requests_clarification_without_review(system):
    from app.workflows.checkpoints import setup

    setup(system["engine"])
    run = create(system, "w")
    assert run_support(system)
    result = system["client"].get(base(system, run)).json()
    assert result["state"] == "completed" and result["outcome"] == "clarification_needed"
    assert result["handoff"] is None and result["retrieval_id"] is None
    assert "describe" in result["draft"]


def test_missing_sources_is_distinct_from_review(system):
    from app.workflows.checkpoints import setup

    setup(system["engine"])
    run = create(system)
    assert run_support(system)
    result = system["client"].get(base(system, run)).json()
    assert result["state"] == "completed" and result["outcome"] == "insufficient_evidence"
    assert result["handoff"] is None


def test_response_idempotency_context_binding_and_exact_citations(system):
    prepare(system)
    run = create(system)
    run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    endpoint = path + f"/development-handoff/{handoff['id']}"
    payload = draft_payload(handoff)
    assert client.post(endpoint, headers=auth, json={**payload, "context_hash": "0" * 64}).status_code == 409
    assert (
        client.post(
            endpoint,
            headers=auth,
            json={**payload, "citations": [{"chunk_id": str(uuid.uuid4()), "quote": "fake"}]},
        ).status_code
        == 422
    )
    assert client.post(endpoint, headers=auth, json=payload).status_code == 202
    assert client.post(endpoint, headers=auth, json=payload).status_code == 202
    assert (
        client.post(endpoint, headers=auth, json={**payload, "answer": "A conflicting response"}).status_code
        == 409
    )
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Handoff)) == 1
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "support_run")) == 2
