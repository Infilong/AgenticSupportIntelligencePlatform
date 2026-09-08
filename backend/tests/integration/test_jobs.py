from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.jobs.queue import LeaseLost, claim, enqueue, finish, heartbeat, request_cancel
from app.modules.workspaces.models import Membership
from app.modules.workspaces.service import change_member
from app.worker import run_once


def submit(system, key="test", payload=None, role="operator"):
    with Session(system["engine"], expire_on_commit=False) as db, db.begin():
        job = enqueue(db, system["workspace"], system["users"][role].id, "database_check", key, payload or {})
    return job.id


def take(engine):
    with Session(engine, expire_on_commit=False) as db, db.begin():
        return claim(db)


def test_idempotency_payload_and_permission_boundaries(system):
    job_id = submit(system)
    assert submit(system) == job_id
    with pytest.raises(HTTPException) as error:
        submit(system, payload={"different": True})
    assert error.value.status_code == 409
    for role in ("viewer", "other"):
        with pytest.raises(HTTPException):
            submit(system, key=role, role=role)


def test_concurrent_claims_never_share_a_job(system):
    ids = {submit(system, key=str(number)) for number in range(4)}
    barrier = Barrier(4)

    def contend(_):
        barrier.wait(timeout=10)
        return take(system["engine"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs = list(pool.map(contend, range(4)))
    assert {job.id for job in jobs} == ids
    assert len({job.lease_token for job in jobs}) == 4
    assert take(system["engine"]) is None


def test_expired_takeover_fences_old_worker_and_heartbeat(system):
    job_id = submit(system)
    old = take(system["engine"])
    with Session(system["engine"]) as db, db.begin():
        row = db.get(Job, job_id)
        row.lease_expires_at = db.scalar(select(func.now())) - timedelta(seconds=1)
    replacement = take(system["engine"])
    assert replacement.id == old.id and replacement.attempts == 2
    assert replacement.lease_token != old.lease_token
    for action in (heartbeat, finish):
        with pytest.raises(LeaseLost), Session(system["engine"]) as db, db.begin():
            action(db, job_id, old.lease_token)
    with Session(system["engine"]) as db, db.begin():
        assert heartbeat(db, job_id, replacement.lease_token)
        assert finish(db, job_id, replacement.lease_token, result={"real": True}).state == "succeeded"


def test_cancellation_and_retry_are_bounded(system):
    job_id = submit(system)
    running = take(system["engine"])
    with Session(system["engine"]) as db, db.begin():
        with pytest.raises(HTTPException):
            request_cancel(db, system["foreign"], system["users"]["other"].id, job_id)
        request_cancel(db, system["workspace"], system["users"]["operator"].id, job_id)
        assert not heartbeat(db, job_id, running.lease_token)
        assert finish(db, job_id, running.lease_token, result={"must_not_publish": True}).state == "cancelled"
        assert db.get(Job, job_id).result is None
    retry_id = submit(system, key="retry")
    for attempt in range(1, 4):
        job = take(system["engine"])
        with Session(system["engine"]) as db, db.begin():
            row = finish(db, retry_id, job.lease_token, error_code="temporary", retry=True)
            assert row.attempts == attempt
            assert row.state == ("failed" if attempt == 3 else "queued")
            row.available_at = db.scalar(select(func.now())) - timedelta(seconds=1)
    assert take(system["engine"]) is None


def test_worker_real_diagnostic_and_revoked_actor(system, caplog):
    job_id = submit(system)
    assert run_once(system["engine"])
    with Session(system["engine"]) as db:
        row = db.get(Job, job_id)
        assert row.state == "succeeded"
        assert row.result["database"] == "reachable"
        assert row.result["vector_version"]
    denied_id = submit(system, key="revoked")
    with Session(system["engine"]) as db, db.begin():
        db.delete(db.get(Membership, (system["workspace"], system["users"]["operator"].id)))
    calls = []
    assert run_once(system["engine"], handlers={"database_check": lambda *_: calls.append(True)})
    assert calls == []
    with Session(system["engine"]) as db:
        row = db.get(Job, denied_id)
        assert row.state == "failed" and row.error_code == "actor_access_revoked"


def test_exhausted_expired_job_is_terminal(system):
    job_id = submit(system)
    with Session(system["engine"]) as db, db.begin():
        row = db.get(Job, job_id)
        row.state = "running"
        row.attempts = row.max_attempts
        row.lease_expires_at = db.scalar(select(func.now())) - timedelta(seconds=1)
    assert take(system["engine"]) is None
    with Session(system["engine"]) as db:
        row = db.get(Job, job_id)
        assert row.state == "failed" and row.error_code == "lease_attempts_exhausted"


def test_concurrent_enqueue_and_surrounding_rollback(system):
    barrier = Barrier(2)

    def contend(_):
        barrier.wait(timeout=10)
        return submit(system, key="concurrent")

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert len(set(pool.map(contend, range(2)))) == 1
    with Session(system["engine"]) as db:
        enqueue(db, system["workspace"], system["users"]["operator"].id, "database_check", "rollback", {})
        db.rollback()
        assert db.scalar(select(Job).where(Job.idempotency_key == "rollback")) is None


@pytest.mark.parametrize("action", ["revoke", "cancel"])
def test_intervention_during_handler_prevents_publication(system, action):
    job_id = submit(system)
    entered, release = Event(), Event()

    def handler(*_):
        entered.set()
        assert release.wait(timeout=15)
        return {"must_not_publish": True}

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(run_once, system["engine"], {"database_check": handler})
        try:
            assert entered.wait(timeout=10)
            with Session(system["engine"]) as db, db.begin():
                if action == "revoke":
                    change_member(
                        db,
                        system["workspace"],
                        system["users"]["admin"].id,
                        system["users"]["operator"].id,
                        None,
                    )
                else:
                    request_cancel(db, system["workspace"], system["users"]["admin"].id, job_id)
        finally:
            release.set()
        assert future.result(timeout=10)
    with Session(system["engine"]) as db:
        job = db.get(Job, job_id)
        assert job.state == ("failed" if action == "revoke" else "cancelled")
        assert job.result is None
