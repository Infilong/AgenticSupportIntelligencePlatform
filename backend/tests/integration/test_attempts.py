import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.attempts import AttemptInput
from app.modules.support.attempts import create as create_attempt
from app.modules.support.models import Message, SupportRun
from app.workflows.checkpoints import setup
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, prepare, run_support


def child(
    system, run, action="clarify", details="What is the refund deadline?", key="child-1", role="operator"
):
    return system["client"].post(
        base(system, run) + "/attempts",
        headers={**login(system["client"], role), "Idempotency-Key": key},
        json={"action": action, **({"clarification": details} if action == "clarify" else {})},
    )


def test_clarification_preserves_original_and_history_with_one_latest_inbox_row(system):
    prepare(system)
    first = create(system, original="w")
    assert run_support(system)
    response = child(system, first)
    assert response.status_code == 202, response.text
    second = response.json()
    assert child(system, first).json() == second
    assert run_support(system), system.get("claim_diagnostic")
    detail = system["client"].get(base(system, second)).json()
    assert detail["original"] == "w" and detail["clarification"] == "What is the refund deadline?"
    assert detail["input_text"].startswith("w\n") and detail["state"] == "waiting_for_input"
    assert detail["retrieval_id"] and detail["handoff"]
    assert detail["parent_run_id"] == first["run_id"] and detail["attempt_number"] == 2
    assert [row["number"] for row in detail["attempts"]] == [1, 2]
    inbox = system["client"].get(f"/api/workspaces/{system['workspace']}/messages?limit=1").json()
    assert (
        inbox["total"] == 1 and len(inbox["items"]) == 1 and inbox["items"][0]["run_id"] == second["run_id"]
    )
    original = system["client"].get(base(system, first)).json()
    assert original["outcome"] == "clarification_needed" and original["latest_run_id"] == second["run_id"]
    assert create(system, original="w") == first  # Initial submission replay still selects attempt one.
    assert child(system, first, key="stale-parent").status_code == 409


@pytest.mark.parametrize("terminal", ["cancelled", "failed"])
def test_retry_uses_fresh_job_and_exact_previous_input(system, terminal):
    prepare(system)
    first = create(system)
    if terminal == "cancelled":
        assert (
            system["client"]
            .post(base(system, first) + "/cancel", headers=login(system["client"], "operator"))
            .status_code
            == 200
        )
    else:
        with Session(system["engine"]) as db, db.begin():
            job = db.get(Job, uuid.UUID(first["job_id"]))
            job.state, job.error_code = "failed", "synthetic_provider_failure"
    response = child(system, first, action="retry")
    assert response.status_code == 202, response.text
    second = response.json()
    assert second["job_id"] != first["job_id"] and second["run_id"] != first["run_id"]
    assert run_support(system)
    old = system["client"].get(base(system, first)).json()
    new = system["client"].get(base(system, second)).json()
    assert new["input_text"] == old["input_text"] and new["state"] == "waiting_for_input"
    assert old["state"] == terminal and new["review"] is None and new["reviewed_response"] is None


def test_competing_children_have_one_winner_and_no_duplicate_message(system):
    setup(system["engine"])
    first = create(system, original="w")
    assert run_support(system)

    def contend(number):
        try:
            with Session(system["engine"]) as db, db.begin():
                create_attempt(
                    db,
                    system["workspace"],
                    system["users"]["operator"].id,
                    uuid.UUID(first["run_id"]),
                    f"competing-{number}",
                    AttemptInput(action="clarify", clarification="Refund question"),
                )
            return 202
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(contend, range(2))) == [202, 409]
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Message)) == 1
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 2
        assert db.scalar(select(func.count()).select_from(Job)) == 2


def test_active_attempt_and_oversize_input_rejected_without_partial_child(system):
    first = create(system, original="a" * 990)
    assert child(system, first).status_code == 409
    assert (
        system["client"]
        .post(base(system, first) + "/cancel", headers=login(system["client"], "operator"))
        .status_code
        == 200
    )
    assert child(system, first).status_code == 422
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 1


@pytest.mark.parametrize("retry", [False, True])
def test_meaningless_added_details_do_not_gain_meaning_from_the_context_label(system, retry):
    setup(system["engine"])
    first = create(system, original="w")
    assert run_support(system)
    response = child(system, first, details="w")
    assert response.status_code == 202
    if retry:
        current = response.json()
        assert (
            system["client"]
            .post(base(system, current) + "/cancel", headers=login(system["client"], "operator"))
            .status_code
            == 200
        )
        response = child(system, current, action="retry", key="retry-meaningless")
        assert response.status_code == 202
    assert run_support(system)
    result = system["client"].get(base(system, response.json())).json()
    assert result["outcome"] == "clarification_needed" and result["model_calls"] == []
