"""Real persisted handoff identities, legacy migration and fenced development replay."""

import uuid
from copy import deepcopy
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.jobs.contracts import RetryableJobError
from app.jobs.models import Job
from app.modules.support.context import digest
from app.modules.support.models import Handoff
from app.modules.usage.models import ModelCall
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, draft_payload, prepare, run_support


def waiting(system):
    prepare(system)
    run = create(system)
    assert run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    endpoint = path + f"/development-handoff/{handoff['id']}"
    return run, path, auth, handoff, endpoint


def test_recorded_request_and_langchain_replay_do_not_invent_model_call(system, monkeypatch):
    from app.workflows import support_graph

    run, path, auth, handoff, endpoint = waiting(system)
    request = handoff["generation_request"]
    assert handoff["request_storage"] == "recorded"
    assert handoff["request_hash"] == digest(request)
    assert request["context_hash"] == handoff["context_hash"]
    assert request["messages"][0] == {"role": "system", "content": handoff["context"]["instruction"]}
    assert "refund" in request["messages"][1]["content"]
    with Session(system["engine"]) as db:
        before = db.scalar(select(func.count()).select_from(ModelCall))
    calls = []
    original = support_graph.replay

    class Observe:
        def invoke(self, value):
            calls.append(deepcopy(value))
            return original.invoke(value)

    monkeypatch.setattr(support_graph, "replay", Observe())
    payload = {**draft_payload(handoff), "request_hash": handoff["request_hash"]}
    client = system["client"]
    assert client.post(endpoint, headers=auth, json=payload).status_code == 202
    assert client.post(endpoint, headers=auth, json=payload).status_code == 202
    assert run_support(system)
    result = client.get(path).json()
    assert result["state"] == "awaiting_review"
    assert len(calls) == 1 and calls[0]["request"] == request
    assert calls[0]["response"]["request_hash"] == handoff["request_hash"]
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ModelCall)) == before


def test_wrong_request_hash_is_rejected_before_submission(system):
    _, path, auth, handoff, endpoint = waiting(system)
    response = system["client"].post(
        endpoint, headers=auth, json={**draft_payload(handoff), "request_hash": "0" * 64}
    )
    assert response.status_code == 409
    assert system["client"].get(path).json()["state"] == "waiting_for_input"
    with Session(system["engine"]) as db:
        assert db.get(Handoff, uuid.UUID(handoff["id"])).response is None


@pytest.mark.parametrize("changed", ["context", "generation_request", "response"])
def test_changed_stored_identity_cannot_publish(system, changed):
    _, path, auth, handoff, endpoint = waiting(system)
    assert system["client"].post(endpoint, headers=auth, json=draft_payload(handoff)).status_code == 202
    with Session(system["engine"]) as db, db.begin():
        row = db.get(Handoff, uuid.UUID(handoff["id"]))
        value = deepcopy(getattr(row, changed))
        value["unexpected_mutation"] = True
        setattr(row, changed, value)
    assert run_support(system, expect_failure=True)
    result = system["client"].get(path).json()
    assert result["state"] != "awaiting_review" and result["draft"] is None
    assert any(step["status"] == "failed" for step in result["steps"])


def test_cancellation_during_replay_fences_publication(system, monkeypatch):
    from app.workflows import support_graph

    _, path, auth, handoff, endpoint = waiting(system)
    client = system["client"]
    assert client.post(endpoint, headers=auth, json=draft_payload(handoff)).status_code == 202
    original = support_graph.replay

    class Cancel:
        def invoke(self, value):
            # This would block if the snapshot kept the workspace transaction locked.
            assert client.post(path + "/cancel", headers=auth).status_code == 200
            return original.invoke(value)

    monkeypatch.setattr(support_graph, "replay", Cancel())
    assert run_support(system, expect_failure=True)
    result = client.get(path).json()
    assert result["state"] == "cancelled" and result["draft"] is None


@pytest.mark.parametrize("submitted", [False, True])
def test_existing_handoff_survives_migration_without_invented_request(system, submitted):
    _, path, auth, handoff, endpoint = waiting(system)
    if submitted:
        assert system["client"].post(endpoint, headers=auth, json=draft_payload(handoff)).status_code == 202
    with system["engine"].begin() as connection:
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.attributes["connection"] = connection
        command.downgrade(config, "0014_evaluation_records")
        before = connection.execute(text(
            "SELECT context, context_hash, response, response_hash FROM development_handoffs"
        )).one()
        command.upgrade(config, "head")
        after = connection.execute(text(
            "SELECT context, context_hash, response, response_hash, generation_request, request_hash "
            "FROM development_handoffs"
        )).one()
        assert tuple(after[:4]) == tuple(before) and after[4:] == (None, None)
    if not submitted:
        exported = system["client"].get(path + "/development-handoff").json()
        assert exported["request_storage"] == "reconstructed"
        assert exported["context_hash"] == handoff["context_hash"]
    # Also replay a legacy submission without changing its stored response identity.
    assert system["client"].post(endpoint, headers=auth, json=draft_payload(handoff)).status_code == 202
    assert run_support(system)
    assert system["client"].get(path).json()["state"] == "awaiting_review"


def test_completed_graph_recovery_rejects_changed_response_before_publication(system, monkeypatch):
    from app.modules.support import processing

    _, path, auth, handoff, endpoint = waiting(system)
    client = system["client"]
    assert client.post(endpoint, headers=auth, json=draft_payload(handoff)).status_code == 202
    original, completed = processing.execute, []

    def crash_after_graph(*args, **kwargs):
        result = original(*args, **kwargs)
        completed.append(result)
        if len(completed) == 1:
            assert result["outcome"] == "draft"
            with Session(system["engine"]) as db, db.begin():
                row = db.get(Handoff, uuid.UUID(handoff["id"]))
                row.response = {**row.response, "answer": "Changed after graph completion"}
            raise RetryableJobError("Synthetic retryable loss after completed graph")
        return result

    monkeypatch.setattr(processing, "execute", crash_after_graph)
    assert run_support(system, expect_failure=True)
    with Session(system["engine"]) as db, db.begin():
        job = db.get(Job, uuid.UUID(client.get(path).json()["job_id"]))
        assert job.state == "queued"
        job.available_at = db.scalar(select(func.clock_timestamp())) - timedelta(seconds=1)
    assert run_support(system, expect_failure=True)
    assert len(completed) == 2 and completed[0] == completed[1]
    result = client.get(path).json()
    assert result["state"] == "failed" and result["draft"] is None
