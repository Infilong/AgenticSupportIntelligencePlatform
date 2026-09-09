from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.reviews.models import ReviewDecision
from app.modules.reviews.schemas import ReviewInput
from app.modules.reviews.service import submit
from app.modules.support.models import SupportRun
from tests.integration.conftest import login
from tests.integration.review_helpers import decision_payload, ready_draft, run_review


@pytest.mark.parametrize("action", ["approve", "edit", "reject"])
def test_operator_review_preserves_draft_and_publishes_separate_final(system, action):
    path, draft = ready_draft(system)
    client, auth = system["client"], login(system["client"], "operator")
    payload = decision_payload(draft, action)
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    worked, errors = run_review(system)
    assert worked and not errors, errors
    final = client.get(path).json()
    assert final["draft"] == draft["draft"] and final["citations"] == draft["citations"]
    assert final["outcome"] == ("rejected_response" if action == "reject" else "approved_response")
    expected = None if action == "reject" else payload.get("response", draft["draft"])
    assert final["reviewed_response"] == expected
    assert final["review"]["actor_id"] == str(system["users"]["operator"].id)
    assert final["review"]["reason"] == payload["reason"]
    assert final["review_version"] == 1
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ReviewDecision)) == 1
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "support_review")) == 1


def test_review_permissions_and_draft_binding(system):
    path, draft = ready_draft(system, "policy_exception")
    client = system["client"]
    payload = decision_payload(draft)
    assert draft["outcome"] == "policy_review_required"
    for role in ("viewer", "operator"):
        auth = login(client, role)
        assert client.post(path + "/review", headers=auth, json=payload).status_code == 403
    auth = login(client)
    assert (
        client.post(path + "/review", headers=auth, json={**payload, "draft_hash": "0" * 64}).status_code
        == 409
    )
    assert (
        client.post(path + "/review", headers=auth, json={**payload, "expected_revision": 1}).status_code
        == 409
    )
    assert client.post(path + "/review", headers=auth, json=payload).status_code == 202
    worked, errors = run_review(system)
    assert worked and not errors, errors
    assert client.get(path).json()["outcome"] == "approved_response"


def test_competing_reviews_have_one_winner_and_one_job(system):
    path, draft = ready_draft(system)
    with Session(system["engine"]) as db:
        run_id = db.scalar(select(SupportRun.id))

    def decide(action):
        try:
            with Session(system["engine"]) as db, db.begin():
                submit(
                    db,
                    system["workspace"],
                    system["users"]["operator"].id,
                    run_id,
                    ReviewInput(**decision_payload(draft, action)),
                )
            return 202
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(decide, ["approve", "reject"])) == [202, 409]
    worked, errors = run_review(system)
    assert worked and not errors, errors
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(ReviewDecision)) == 1
        assert db.scalar(select(func.count()).select_from(Job).where(Job.kind == "support_review")) == 1
