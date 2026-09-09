from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.knowledge.retrieval import retrieve
from app.modules.support.processing import process
from app.worker import run_once
from app.workflows.checkpoints import setup
from tests.integration.conftest import login
from tests.integration.job_readiness import wait_initial
from tests.integration.test_knowledge import TestEmbeddings, add_version, ingest
from tests.integration.test_retrieval import TestReranker


def prepare(system):
    setup(system["engine"])
    version = add_version(system)
    assert ingest(system)
    return version


def create(system, original="What is the refund deadline?", language="en", role="operator", key="message-1"):
    client, ws = system["client"], system["workspace"]
    auth = login(client, role)
    response = client.post(
        f"/api/workspaces/{ws}/messages",
        headers={**auth, "Idempotency-Key": key},
        json={"original": original, "language": language},
    )
    assert response.status_code == 202, response.text
    return response.json()


def fake_retrieval(engine, workspace_id, actor_id, query, **kwargs):
    return retrieve(
        engine,
        workspace_id,
        actor_id,
        query,
        provider=TestEmbeddings(),
        ranking_provider=TestReranker(),
        **kwargs,
    )


def run_support(system, expect_failure=False):
    errors = []

    def handler(engine, job):
        try:
            return process(engine, job, retrieval=fake_retrieval)
        except Exception as error:
            errors.append(error)
            raise

    wait_initial(system, "support_run")
    worked = run_once(system["engine"], handlers={"support_run": handler})
    if errors and not expect_failure:
        raise errors[0]
    if not worked and not expect_failure:
        with Session(system["engine"]) as db:
            rows = db.execute(
                select(Job.id, Job.state, Job.attempts, Job.available_at, Job.cancel_requested)
            ).all()
            now = db.scalar(select(func.clock_timestamp()))
        system["claim_diagnostic"] = f"database time={now}; jobs={rows}"
    return worked


def base(system, run):
    return f"/api/workspaces/{system['workspace']}/runs/{run['run_id']}"


def draft_payload(handoff, answer="The policy allows fourteen days to request a refund."):
    source = handoff["context"]["sources"][0]
    return {
        "context_hash": handoff["context_hash"],
        "answer": answer,
        "citations": [{"chunk_id": source["chunk_id"], "quote": source["text"]}],
    }
