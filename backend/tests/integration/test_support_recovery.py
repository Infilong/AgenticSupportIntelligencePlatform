from datetime import timedelta

import psycopg
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.models import Handoff
from tests.integration.conftest import login
from tests.integration.support_helpers import base, create, draft_payload, prepare, run_support


def test_failed_development_resume_recovers_the_stored_contribution(system, monkeypatch):
    from app.workflows import support_graph

    prepare(system)
    run = create(system)
    assert run_support(system)
    client, path = system["client"], base(system, run)
    auth = login(client)
    handoff = client.get(path + "/development-handoff").json()
    payload = draft_payload(handoff)
    assert (
        client.post(path + f"/development-handoff/{handoff['id']}", headers=auth, json=payload).status_code
        == 202
    )
    validate, attempts = support_graph.validate_sources, 0

    def interrupted(*args):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise psycopg.OperationalError("Synthetic source-check connection failure")
        return validate(*args)

    monkeypatch.setattr(support_graph, "validate_sources", interrupted)
    assert run_support(system, expect_failure=True)
    with Session(system["engine"]) as db, db.begin():
        job = db.get(Job, client.get(path).json()["job_id"])
        assert job.state == "queued" and job.attempts == 1
        job.available_at = db.scalar(select(func.clock_timestamp())) - timedelta(seconds=1)
    assert run_support(system), system.get("claim_diagnostic")
    final = client.get(path).json()
    assert final["state"] == "awaiting_review" and final["draft"] == payload["answer"]
    with Session(system["engine"]) as db:
        assert db.scalar(select(func.count()).select_from(Handoff)) == 1
