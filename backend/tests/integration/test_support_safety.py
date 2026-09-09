import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import psycopg
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.contracts import RetryableJobError
from app.jobs.models import Job
from app.jobs.queue import LeaseLost, claim
from app.modules.knowledge.service import set_withdrawn
from app.modules.support.models import Handoff, RunStep, SupportRun
from app.modules.support.processing import process
from app.modules.support.schemas import DevelopmentResponse
from app.modules.support.service import submit_response
from app.modules.workspaces.service import change_member
from app.worker import run_once
from app.workflows.checkpoints import locked_graph
from tests.integration.conftest import login
from tests.integration.support_helpers import (
    base,
    create,
    draft_payload,
    fake_retrieval,
    prepare,
    run_support,
)
from tests.integration.test_knowledge import add_version, ingest


def waiting(system):
    prepare(system)
    run = create(system)
    run_support(system)
    auth = login(system["client"])
    path = base(system, run)
    handoff = system["client"].get(path + "/development-handoff").json()
    return run, path, handoff, auth


def test_cancel_waiting_then_submission_cannot_restart(system):
    run, path, handoff, auth = waiting(system)
    client = system["client"]
    assert client.post(path + "/cancel", headers=auth).json()["state"] == "cancelled"
    assert (
        client.post(
            path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff)
        ).status_code
        == 409
    )
    assert client.get(path + "/development-handoff").status_code == 409
    assert not run_support(system)
    assert client.get(path).json()["draft"] is None


def test_original_requester_demotion_blocks_admin_resume(system):
    _, path, handoff, auth = waiting(system)
    with Session(system["engine"]) as db:
        change_member(
            db, system["workspace"], system["users"]["admin"].id, system["users"]["operator"].id, "viewer"
        )
    assert (
        system["client"]
        .post(path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff))
        .status_code
        == 403
    )
    assert system["client"].get(path + "/development-handoff").status_code == 403


def test_uncited_withdrawn_context_blocks_submission_and_export(system):
    prepare(system)
    add_version(system, b"# Additional policy\nSupport hours are nine to five.")
    assert ingest(system)
    run = create(system)
    run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    assert len(handoff["context"]["sources"]) == 2
    cited = handoff["context"]["sources"][0]
    uncited = handoff["context"]["sources"][1]
    assert cited["chunk_id"] != uncited["chunk_id"]
    with Session(system["engine"]) as db:
        set_withdrawn(
            db, system["workspace"], system["users"]["admin"].id, uuid.UUID(uncited["document_id"]), True
        )
        db.commit()
    assert client.get(path + "/development-handoff").status_code == 409
    assert (
        client.post(
            path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff)
        ).status_code
        == 409
    )


def test_source_change_after_submission_prevents_publication(system):
    run, path, handoff, auth = waiting(system)
    client = system["client"]
    assert (
        client.post(
            path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff)
        ).status_code
        == 202
    )
    with Session(system["engine"]) as db:
        set_withdrawn(
            db,
            system["workspace"],
            system["users"]["admin"].id,
            uuid.UUID(handoff["context"]["sources"][0]["document_id"]),
            True,
        )
        db.commit()
    assert run_support(system, expect_failure=True)
    result = client.get(path).json()
    assert result["state"] == "failed" and result["draft"] is None
    assert result["error_code"] == "request_rejected_409"


@pytest.mark.parametrize("identical", [True, False])
def test_concurrent_contributions_create_only_one_resume_job(system, identical):
    run, _, handoff, _ = waiting(system)

    def contribute(index):
        data = draft_payload(handoff, "Same answer" if identical else f"Answer {index}")
        try:
            with Session(system["engine"]) as db, db.begin():
                submit_response(
                    db,
                    system["workspace"],
                    system["users"]["admin"].id,
                    uuid.UUID(run["run_id"]),
                    uuid.UUID(handoff["id"]),
                    DevelopmentResponse.model_validate(data),
                )
            return 202
        except HTTPException as error:
            return error.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(contribute, range(2))) == ([202, 202] if identical else [202, 409])
    with Session(system["engine"]) as db:
        assert (
            db.scalar(select(func.count()).select_from(Job).where(Job.idempotency_key.like("resume:%"))) == 1
        )


@pytest.mark.parametrize("completed", [False, True])
def test_checkpoint_before_domain_publication_replays_once(system, completed):
    prepare(system)
    run = create(system)
    if completed:
        run_support(system)
        client, path = system["client"], base(system, run)
        auth = login(client)
        handoff = client.get(path + "/development-handoff").json()
        assert (
            client.post(
                path + f"/development-handoff/{handoff['id']}", headers=auth, json=draft_payload(handoff)
            ).status_code
            == 202
        )
    with Session(system["engine"], expire_on_commit=False) as db, db.begin():
        job = claim(db)
    publication = process(system["engine"], job, retrieval=fake_retrieval)
    # Simulate loss after checkpoint commit, before the publication transaction.
    with Session(system["engine"]) as db, db.begin():
        current = db.get(Job, job.id)
        current.lease_expires_at = db.scalar(select(func.now())) - timedelta(seconds=1)
        db.add(
            RunStep(
                workspace_id=job.workspace_id,
                run_id=uuid.UUID(run["run_id"]),
                job_id=job.id,
                job_attempt=job.attempts,
                node="interrupted_test_step",
            )
        )
    with Session(system["engine"]) as db, db.begin(), pytest.raises(LeaseLost):
        publication.publish(db, job)
    assert run_support(system)
    result = system["client"].get(base(system, run)).json()
    assert result["state"] == ("awaiting_review" if completed else "waiting_for_input"), result
    assert any(s["status"] == "uncertain" for s in result["steps"])
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Handoff)) == 1
        assert db.scalar(select(func.count()).select_from(SupportRun)) == 1


def test_checkpoint_connection_failure_is_retryable_and_lock_released(system):
    run_id = uuid.uuid4()
    with pytest.raises(RetryableJobError):
        with locked_graph(system["engine"], run_id):
            raise psycopg.OperationalError("synthetic connection failure")
    with locked_graph(system["engine"], run_id):
        pass


def test_worker_retries_after_durable_interrupt_without_retrieving_again(system):
    prepare(system)
    run = create(system)

    def handler(engine, job):
        process(engine, job, retrieval=fake_retrieval)
        raise RetryableJobError("synthetic failure after durable interrupt")

    assert run_once(system["engine"], handlers={"support_run": handler})
    with Session(system["engine"]) as db, db.begin():
        job = db.get(Job, uuid.UUID(run["job_id"]))
        assert job.state == "queued"
        job.available_at = db.scalar(select(func.clock_timestamp()))
    assert run_support(system)
    result = system["client"].get(base(system, run)).json()
    assert result["state"] == "waiting_for_input"
    assert sum(step["node"] == "retrieve_evidence" for step in result["steps"]) == 1
