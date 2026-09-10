"""Real database/graph/ranking checks; only embedding inference is deterministic here."""

import json

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.comparisons.processing import process as baseline
from app.modules.knowledge.models import Document
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.support.processing import process as support
from app.modules.workspaces.models import Membership
from app.worker import run_once
from app.workflows.checkpoints import setup
from tests.integration.conftest import login
from tests.integration.job_readiness import wait_initial
from tests.integration.support_helpers import fake_retrieval, prepare


def create(system, question="What is the refund deadline?"):
    client = system["client"]
    auth = login(client)
    path = f"/api/workspaces/{system['workspace']}/comparisons"
    response = client.post(
        path,
        headers={**auth, "Idempotency-Key": "comparison-1"},
        json={"original": question, "language": "en"},
    )
    assert response.status_code == 202, response.text
    return path + "/" + response.json()["id"], auth


def work(system, count=4):
    errors = []

    def execute(fn):
        def handler(engine, job):
            try:
                return fn(engine, job, retrieval=fake_retrieval)
            except Exception as error:
                errors.append(error)
                raise

        return handler

    for _ in range(count):
        wait_initial(system, "comparison_prepare")
        wait_initial(system, "support_run")
        assert run_once(
            system["engine"],
            handlers={"comparison_prepare": execute(baseline), "support_run": execute(support)},
        )
    assert not errors, errors


def payload(request):
    sources = json.loads(request["generation_request"]["messages"][1]["content"])["sources"]
    return {
        "context_hash": request["context_hash"],
        "request_hash": request["request_hash"],
        "answer": "A development contribution.",
        "citations": [{"chunk_id": sources[0]["chunk_id"], "quote": sources[0]["text"]}] if sources else [],
    }


def test_four_distinct_pipelines_and_bound_contributions(system):
    prepare(system)
    path, auth = create(system)
    repeated, auth = create(system)
    assert repeated == path
    work(system)
    client = system["client"]
    result = client.get(path).json()
    items = {p["name"]: p for p in result["pipelines"]}
    assert len(items) == 4 and result["comparable"]
    system_run = client.get(f"/api/workspaces/{system['workspace']}/runs/{items['system_v1']['run_id']}")
    assert system_run.status_code == 200 and system_run.json()["input_frozen"] is True
    assert items["direct_llm"]["retrieval_id"] is None
    with Session(system["engine"]) as db:
        traces = list(db.scalars(select(RetrievalTrace)))
        assert sorted(t.strategy for t in traces) == ["hybrid-v1", "hybrid-v1", "vector-v1"]
    for name in items:
        exported = client.get(f"{path}/{name}/request")
        assert exported.status_code == 200, exported.text
        request = exported.json()
        assert set(request) == {"generation_request", "request_hash", "context_hash"}
        data = payload(request)
        endpoint = f"{path}/{name}/response"
        if name == "system_v1":
            assert client.post(endpoint, headers=auth, json={**data, "citations": []}).status_code == 422
        assert client.post(endpoint, headers=auth, json={**data, "request_hash": "0" * 64}).status_code == 409
        assert client.post(endpoint, headers=auth, json=data).status_code == 202
        assert client.post(endpoint, headers=auth, json=data).status_code == 202
        assert client.post(endpoint, headers=auth, json={**data, "answer": "Changed"}).status_code == 409
    work(system, 1)
    items = {p["name"]: p for p in client.get(path).json()["pipelines"]}
    assert items["system_v1"]["state"] == "awaiting_review"
    assert all(items[n]["state"] == "completed" for n in items if n != "system_v1")
    assert all(p["initial_response"] and p["reviewed_response"] is None for p in items.values())


@pytest.mark.parametrize(
    "question,outcome", [("w", "clarification_needed"), ("Refund deadline?", "insufficient_evidence")]
)
def test_empty_corpus_preserves_all_denominators(system, question, outcome):
    setup(system["engine"])
    path, _ = create(system, question)
    work(system)
    items = {p["name"]: p for p in system["client"].get(path).json()["pipelines"]}
    assert len(items) == 4
    assert items["direct_llm"]["state"] == "waiting_for_input"
    assert items["vector_rag"]["state"] == items["hybrid_rag"]["state"] == "insufficient_evidence"
    assert items["system_v1"]["outcome"] == outcome


@pytest.mark.parametrize("role", ["viewer", "operator", "other"])
def test_comparison_permissions_and_input_whitelist(system, role):
    path, _ = create(system)
    auth = login(system["client"], role)
    denied = 404 if role == "other" else 403
    assert system["client"].get(path).status_code == denied
    assert system["client"].post(path + "/cancel", headers=auth).status_code == denied


def test_cancel_and_corpus_change_deny_export_submission_and_system_resume(system):
    prepare(system)
    path, auth = create(system)
    work(system)
    client = system["client"]
    request = client.get(path + "/direct_llm/request").json()
    with Session(system["engine"]) as db, db.begin():
        document = db.scalar(select(Document).where(Document.workspace_id == system["workspace"]))
        document.withdrawn = True
    assert not client.get(path).json()["comparable"]
    for name in ("direct_llm", "vector_rag", "hybrid_rag", "system_v1"):
        assert client.get(f"{path}/{name}/request").status_code == 409
        assert client.post(f"{path}/{name}/response", headers=auth, json=payload(request)).status_code == 409
    assert client.post(path + "/cancel", headers=auth).status_code == 200
    cancelled = client.get(path).json()
    assert cancelled["cancelled"]
    assert all(p["state"] == "cancelled" for p in cancelled["pipelines"])
    assert client.get(path + "/direct_llm/request").status_code == 409


def test_frozen_inputs_reject_scoring_fields_and_revoked_creator(system):
    prepare(system)
    path, auth = create(system)
    work(system)
    client = system["client"]
    root = path.rsplit("/", 1)[0]
    assert (
        client.post(
            root,
            headers={**auth, "Idempotency-Key": "bad-input"},
            json={"original": "Question", "language": "en", "expected_answer": "Leaked rubric"},
        ).status_code
        == 422
    )
    item = next(p for p in client.get(path).json()["pipelines"] if p["name"] == "system_v1")
    assert (
        client.post(
            f"/api/workspaces/{system['workspace']}/runs/{item['run_id']}/attempts",
            headers={**auth, "Idempotency-Key": "retry-frozen"},
            json={"action": "clarify", "clarification": "Changed question"},
        ).status_code
        == 409
    )
    with Session(system["engine"]) as db, db.begin():
        member = db.scalar(
            select(Membership).where(
                Membership.workspace_id == system["workspace"],
                Membership.user_id == system["users"]["admin"].id,
            )
        )
        member.role = "viewer"
    assert client.get(path + "/direct_llm/request").status_code == 403
    assert client.post(path + "/cancel", headers=auth).status_code == 403
