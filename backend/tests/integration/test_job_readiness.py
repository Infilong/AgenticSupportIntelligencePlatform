from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from tests.integration.job_readiness import wait_initial
from tests.integration.test_jobs import submit


def test_future_initial_job_waits_without_claiming_or_changing_its_timestamp(system):
    job_id = submit(system)
    with Session(system["engine"]) as db, db.begin():
        when = db.scalar(select(func.clock_timestamp())) + timedelta(milliseconds=200)
        db.get(Job, job_id).available_at = when
    assert wait_initial(system, "database_check")
    with Session(system["engine"]) as db:
        job = db.get(Job, job_id)
        assert job.state == "queued" and job.attempts == 0 and job.available_at == when
        assert db.scalar(select(func.clock_timestamp())) >= when
    assert system["job_readiness"][0]["job_id"] == str(job_id)


def test_due_absent_and_retry_jobs_do_not_wait(system):
    assert not wait_initial(system, "database_check", max_wait=0)
    job_id = submit(system)
    with Session(system["engine"]) as db, db.begin():
        db.get(Job, job_id).available_at = db.scalar(select(func.clock_timestamp())) - timedelta(seconds=10)
    assert wait_initial(system, "database_check", max_wait=0)
    with Session(system["engine"]) as db, db.begin():
        job = db.get(Job, job_id)
        job.attempts = 1
        job.available_at = db.scalar(select(func.clock_timestamp())) + timedelta(minutes=1)
    assert not wait_initial(system, "database_check", max_wait=0)
    assert not system.get("job_readiness")


def test_readiness_deadline_retains_identity_and_does_not_change_job(system):
    job_id = submit(system)
    with Session(system["engine"]) as db, db.begin():
        db.get(Job, job_id).available_at = db.scalar(select(func.clock_timestamp())) + timedelta(minutes=1)
    with pytest.raises(AssertionError) as error:
        wait_initial(system, "database_check", max_wait=0.01)
    assert str(job_id) in str(error.value) and "last_database_time" in str(error.value)
    with Session(system["engine"]) as db:
        job = db.get(Job, job_id)
        assert job.attempts == 0 and job.state == "queued"
