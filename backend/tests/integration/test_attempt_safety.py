import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.reviews.schemas import ReviewInput
from app.modules.reviews.service import submit
from app.modules.support.attempts import AttemptInput
from app.modules.support.attempts import create as create_attempt
from app.modules.support.models import SupportRun
from app.modules.workspaces.models import Membership
from app.modules.workspaces.service import change_member
from tests.integration.conftest import login
from tests.integration.review_helpers import decision_payload, ready_draft
from tests.integration.support_helpers import base, create, prepare, run_support
from tests.integration.test_attempts import child


def test_viewer_foreign_and_revoked_creator_cannot_process_child(system):
    prepare(system)
    first = create(system, original="w", role="admin")
    assert run_support(system)
    assert child(system, first, role="viewer").status_code == 403
    assert child(system, first, role="other").status_code == 404
    response = child(system, first)
    assert response.status_code == 202
    with Session(system["engine"]) as db:
        change_member(
            db, system["workspace"], system["users"]["admin"].id, system["users"]["operator"].id, "viewer"
        )
    assert run_support(system, expect_failure=True)
    login(system["client"], "admin")
    final = system["client"].get(base(system, response.json())).json()
    assert final["state"] == "failed" and final["retrieval_id"] is None
    assert child(system, first).status_code == 403  # Idempotency cannot bypass current authority.


def test_new_attempt_does_not_inherit_revoked_parent_contributor(system):
    path, _ = ready_draft(system)
    with Session(system["engine"]) as db, db.begin():
        db.add(
            Membership(workspace_id=system["workspace"], user_id=system["users"]["other"].id, role="admin")
        )
    with Session(system["engine"]) as db:
        change_member(
            db, system["workspace"], system["users"]["other"].id, system["users"]["admin"].id, "viewer"
        )
    first = {"run_id": path.rsplit("/", 1)[1]}
    response = child(system, first)
    assert response.status_code == 202, response.text
    assert run_support(system)
    final = system["client"].get(base(system, response.json())).json()
    assert final["state"] == "waiting_for_input" and final["review"] is None
    assert system["client"].get(path).json()["state"] == "cancelled"


def test_review_racing_clarification_cannot_approve_superseded_draft(system):
    path, draft = ready_draft(system)
    run_id = uuid.UUID(path.rsplit("/", 1)[1])

    def contend(action):
        try:
            with Session(system["engine"]) as db, db.begin():
                if action == "review":
                    submit(
                        db,
                        system["workspace"],
                        system["users"]["operator"].id,
                        run_id,
                        ReviewInput(**decision_payload(draft)),
                    )
                else:
                    create_attempt(
                        db,
                        system["workspace"],
                        system["users"]["operator"].id,
                        run_id,
                        "competing-clarification",
                        AttemptInput(action="clarify", clarification="Initial annual purchase"),
                    )
            return 202
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(contend, ["review", "clarify"])) == [202, 409]
    with Session(system["engine"]) as db:
        parent = db.get(SupportRun, run_id)
        assert parent.reviewed_response is None
        assert parent.state in {"queued", "cancelled"}
        assert db.scalar(select(func.count()).select_from(Job).where(Job.state == "queued")) == 1


def test_parent_constraint_rejects_cross_message_lineage(system):
    first, second = create(system), create(system, key="separate-message")
    with Session(system["engine"]) as db, db.begin(), pytest.raises(IntegrityError):
        run = db.get(SupportRun, uuid.UUID(second["run_id"]))
        run.parent_run_id, run.attempt_number, run.attempt_kind = uuid.UUID(first["run_id"]), 2, "retry"
        db.flush()


def test_attempt_limit_is_atomic_and_does_not_create_an_eleventh_run(system):
    first = create(system)
    current = first
    for number in range(2, 11):
        with Session(system["engine"]) as db, db.begin():
            db.get(Job, uuid.UUID(str(current["job_id"]))).state = "failed"
            current = create_attempt(
                db,
                system["workspace"],
                system["users"]["operator"].id,
                uuid.UUID(str(current["run_id"])),
                f"retry-{number}",
                AttemptInput(action="retry"),
            )
    with Session(system["engine"]) as db, db.begin():
        db.get(Job, current["job_id"]).state = "failed"
    response = child(system, {"run_id": str(current["run_id"])}, action="retry", key="over-limit")
    assert response.status_code == 409 and "ten-attempt" in response.text
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 10
        assert db.scalar(select(func.count()).select_from(Job)) == 10
