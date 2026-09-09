import uuid
from datetime import timedelta

import psycopg
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.contracts import RetryableJobError
from app.jobs.models import Job
from app.jobs.queue import LeaseLost, claim
from app.modules.knowledge.service import set_withdrawn
from app.modules.reviews.models import ReviewDecision
from app.modules.reviews.processing import process
from app.modules.support.models import SupportRun
from app.modules.workspaces.models import Membership
from app.modules.workspaces.service import change_member
from tests.integration.conftest import login
from tests.integration.review_helpers import decision_payload, ready_draft, run_review


def test_failed_resumed_review_node_recovers_without_duplicate_decision(system, monkeypatch):
    from app.workflows import review_graph

    path, draft = ready_draft(system)
    client, auth = system["client"], login(system["client"], "operator")
    assert client.post(path + "/review", headers=auth, json=decision_payload(draft)).status_code == 202
    original, calls = review_graph.checked_decision, 0
    snapshots = []
    compile_graph = review_graph.StateGraph.compile

    def capture_graph(builder, *args, **kwargs):
        graph = compile_graph(builder, *args, **kwargs)
        get_state = graph.get_state

        def capture(*args, **kwargs):
            saved = get_state(*args, **kwargs)
            snapshots.append(
                (
                    saved.next,
                    list(saved.values),
                    len(saved.interrupts),
                    [(task.name, task.error) for task in saved.tasks],
                )
            )
            return saved

        graph.get_state = capture
        return graph

    monkeypatch.setattr(review_graph.StateGraph, "compile", capture_graph)

    def transient_failure(*args):
        nonlocal calls
        calls += 1
        if calls == 2:  # Fail inside the resumed node, after its preflight succeeds.
            raise psycopg.OperationalError("Synthetic temporary connection loss")
        return original(*args)

    monkeypatch.setattr(review_graph, "checked_decision", transient_failure)
    worked, errors = run_review(system)
    assert worked and len(errors) == 1 and isinstance(errors[0], RetryableJobError)
    with Session(system["engine"]) as db, db.begin():
        job = db.scalar(select(Job).where(Job.kind == "support_review"))
        assert job.state == "queued" and job.attempts == 1
        job.available_at = db.scalar(select(func.clock_timestamp())) - timedelta(seconds=1)
    worked, errors = run_review(system)
    assert worked and not errors, (errors, snapshots)
    final = client.get(path).json()
    assert final["outcome"] == "approved_response"
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ReviewDecision)) == 1


def withdraw_source(system, draft):
    with Session(system["engine"]) as db, db.begin():
        set_withdrawn(
            db,
            system["workspace"],
            system["users"]["admin"].id,
            uuid.UUID(draft["citations"][0]["document_id"]),
            True,
        )


def test_stale_evidence_blocks_approval_but_can_be_rejected(system):
    path, draft = ready_draft(system)
    withdraw_source(system, draft)
    client, auth = system["client"], login(system["client"], "operator")
    assert client.post(path + "/review", headers=auth, json=decision_payload(draft)).status_code == 409
    assert (
        client.post(path + "/review", headers=auth, json=decision_payload(draft, "reject")).status_code == 202
    )
    worked, errors = run_review(system)
    assert worked and not errors, errors
    final = client.get(path).json()
    assert final["outcome"] == "rejected_response" and final["reviewed_response"] is None


@pytest.mark.parametrize("boundary", ["cancel", "withdraw", "revoke_reviewer"])
def test_changed_authority_or_source_after_decision_prevents_publication(system, boundary):
    path, draft = ready_draft(system)
    with Session(system["engine"]) as db, db.begin():
        db.add(
            Membership(workspace_id=system["workspace"], user_id=system["users"]["other"].id, role="operator")
        )
    client, auth = system["client"], login(system["client"], "other")
    assert client.post(path + "/review", headers=auth, json=decision_payload(draft)).status_code == 202
    if boundary == "cancel":
        assert client.post(path + "/cancel", headers=auth).status_code == 200
    elif boundary == "withdraw":
        withdraw_source(system, draft)
    else:
        with Session(system["engine"]) as db, db.begin():
            change_member(
                db, system["workspace"], system["users"]["admin"].id, system["users"]["other"].id, "viewer"
            )
    run_review(system)
    login(client)
    final = client.get(path).json()
    assert final["reviewed_response"] is None
    assert final["state"] == ("cancelled" if boundary == "cancel" else "failed")
    assert final["review"]["action"] == "approve"  # Decision history survives failed publication.


@pytest.mark.parametrize("action", ["approve", "clarify"])
def test_review_checkpoint_replay_after_lost_publication_lease(system, action):
    path, draft = ready_draft(system)
    client, auth = system["client"], login(system["client"], "operator")
    payload = decision_payload(draft, action)
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    with Session(system["engine"], expire_on_commit=False) as db, db.begin():
        job = claim(db)
    publication = process(system["engine"], job)
    with Session(system["engine"]) as db, db.begin():
        current = db.get(Job, job.id)
        current.lease_expires_at = db.scalar(select(func.clock_timestamp())) - timedelta(seconds=1)
    with Session(system["engine"]) as db, db.begin(), pytest.raises(LeaseLost):
        publication.publish(db, job)
    worked, errors = run_review(system)
    assert worked and not errors, errors
    final = client.get(path).json()
    expected = "approved_response" if action == "approve" else "clarification_needed"
    assert final["outcome"] == expected and final["review_version"] == 1
    if action == "clarify":
        assert final["review"]["response"] == payload["response"] and final["reviewed_response"] is None
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 1
