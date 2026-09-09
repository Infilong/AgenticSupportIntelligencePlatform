import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.reviews.models import ReviewDecision
from app.modules.reviews.schemas import ReviewInput
from app.modules.reviews.service import submit
from app.modules.workspaces.models import Membership
from app.modules.workspaces.service import change_member
from tests.integration.conftest import login
from tests.integration.review_helpers import decision_payload, ready_draft, run_review
from tests.integration.support_helpers import run_support
from tests.integration.test_review_safety import withdraw_source

QUESTION = "Was this the first annual purchase or a renewal, and on what date?"


def clarification(draft):
    return {**decision_payload(draft), "action": "clarify", "response": QUESTION}


def test_published_question_preserves_draft_and_customer_reply_starts_fresh_retrieval(system):
    path, draft = ready_draft(system)
    client, auth = system["client"], login(system["client"], "operator")
    payload = clarification(draft)
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    assert client.get(path).json()["outcome"] != "clarification_needed"
    worked, errors = run_review(system)
    assert worked and not errors, errors
    result = client.get(path).json()
    assert result["state"] == "completed" and result["outcome"] == "clarification_needed"
    assert result["reviewed_response"] is None and result["review"]["response"] == QUESTION
    assert result["draft"] == draft["draft"] and result["citations"] == draft["citations"]
    reply = "It was my first annual purchase, made yesterday."
    response = client.post(
        path + "/attempts",
        headers={**auth, "Idempotency-Key": "customer-reply"},
        json={"action": "clarify", "clarification": reply},
    )
    assert response.status_code == 202, response.text
    child_path = path.rsplit("/", 1)[0] + "/" + response.json()["run_id"]
    assert run_support(system), system.get("claim_diagnostic")
    child = client.get(child_path).json()
    assert child["state"] == "waiting_for_input" and child["retrieval_id"] != result["retrieval_id"]
    assert child["review"] is None and child["reviewed_response"] is None and child["draft"] is None
    assert reply in child["input_text"] and QUESTION not in child["input_text"]
    assert child["parent_run_id"] == result["id"] and child["original"] == draft["original"]
    assert client.get(path).json()["review"]["response"] == QUESTION


def test_operator_can_request_details_for_stale_policy_exception_without_approving(system):
    path, draft = ready_draft(system, "policy_exception")
    withdraw_source(system, draft)
    client, auth = system["client"], login(system["client"], "operator")
    assert client.post(path + "/review", headers=auth, json=decision_payload(draft)).status_code == 403
    assert client.post(path + "/review", headers=auth, json=clarification(draft)).status_code == 202
    worked, errors = run_review(system)
    assert worked and not errors, errors
    result = client.get(path).json()
    assert result["outcome"] == "clarification_needed" and result["reviewed_response"] is None
    assert result["review"]["response"] == QUESTION and result["draft"] == draft["draft"]


def test_clarification_requires_authority_and_a_bounded_nonblank_question(system):
    path, draft = ready_draft(system)
    client, payload = system["client"], clarification(draft)
    assert client.post(path + "/review", headers=login(client, "viewer"), json=payload).status_code == 403
    assert client.post(path + "/review", headers=login(client, "other"), json=payload).status_code == 404
    auth = login(client, "operator")
    for question in (None, "", "   ", "bad\x00text", "x" * 1001):
        assert (
            client.post(path + "/review", headers=auth, json={**payload, "response": question}).status_code
            == 422
        )
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ReviewDecision)) == 0


@pytest.mark.parametrize("boundary", ["cancel", "revoke_reviewer"])
def test_question_is_not_published_after_cancellation_or_revocation(system, boundary):
    path, draft = ready_draft(system)
    with Session(system["engine"]) as db, db.begin():
        db.add(
            Membership(workspace_id=system["workspace"], user_id=system["users"]["other"].id, role="operator")
        )
    client, auth = system["client"], login(system["client"], "other")
    assert client.post(path + "/review", headers=auth, json=clarification(draft)).status_code == 202
    if boundary == "cancel":
        assert client.post(path + "/cancel", headers=auth).status_code == 200
    else:
        with Session(system["engine"]) as db, db.begin():
            change_member(
                db, system["workspace"], system["users"]["admin"].id, system["users"]["other"].id, "viewer"
            )
    run_review(system)
    login(client)
    result = client.get(path).json()
    assert result["state"] == ("cancelled" if boundary == "cancel" else "failed")
    assert result["outcome"] != "clarification_needed" and result["reviewed_response"] is None
    assert result["review"]["response"] == QUESTION  # History, not a published next step.


def test_competing_approval_and_clarification_finalize_only_one_decision(system):
    path, draft = ready_draft(system)

    def decide(action):
        payload = clarification(draft) if action == "clarify" else decision_payload(draft)
        try:
            with Session(system["engine"]) as db, db.begin():
                submit(
                    db,
                    system["workspace"],
                    system["users"]["operator"].id,
                    uuid.UUID(draft["id"]),
                    ReviewInput(**payload),
                )
            return 202
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(decide, ["approve", "clarify"])) == [202, 409]
    worked, errors = run_review(system)
    assert worked and not errors, errors
    result = system["client"].get(path).json()
    assert result["outcome"] in {"approved_response", "clarification_needed"}
    assert (result["reviewed_response"] is None) == (result["review"]["action"] == "clarify")
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ReviewDecision)) == 1
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "support_review")) == 1
