"""Local comparison provenance and actual graph execution with deterministic inference."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.comparisons import local_execution
from app.modules.comparisons.models import Pipeline
from app.modules.support import local_response
from app.modules.usage.models import ModelCall
from tests.integration.conftest import login
from tests.integration.support_helpers import prepare
from tests.integration.test_generation_comparisons import work


def answer(request, context):
    sources = context["sources"]
    return {
        "answer": "The policy states fourteen days." if sources else "No company policy supplied.",
        "citations": [{"chunk_id": sources[0]["chunk_id"], "quote": sources[0]["text"]}] if sources else [],
        "review_category": "unclassified",
        "routing": {
            "version": "support-routing-v1",
            "decision": "answer" if sources else "missing",
            "reason": "Evidence checked.",
        },
    }, {"input_tokens": 10, "output_tokens": 8}


def admit(system):
    auth = login(system["client"])
    path = f"/api/workspaces/{system['workspace']}/comparisons"
    response = system["client"].post(
        path,
        headers={**auth, "Idempotency-Key": "local-comparison"},
        json={
            "original": "What is the refund deadline?",
            "language": "en",
            "generation_mode": "local_ollama",
        },
    )
    assert response.status_code == 202, response.text
    return path + "/" + response.json()["id"], auth


def test_local_four_paths_preserve_machine_provenance(system, monkeypatch):
    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    monkeypatch.setattr(local_execution, "generate", answer)
    monkeypatch.setattr(local_response, "generate", answer)
    prepare(system)
    path, auth = admit(system)
    # Admission captures the model; a later runtime configuration cannot change this comparison.
    monkeypatch.setenv("ASI_OLLAMA_MODEL", "changed-after-admission")
    work(system)
    items = {p["name"]: p for p in system["client"].get(path).json()["pipelines"]}
    assert all(p["state"] == "completed" and p["contributor_id"] is None for p in items.values())
    assert items["system_v1"]["outcome"] == "answered"
    assert items["direct_llm"]["retrieval_id"] is None
    assert items["direct_llm"]["initial_response"]["citations"] == []
    with Session(system["engine"]) as db:
        calls = list(db.scalars(select(ModelCall).where(ModelCall.operation == "generate")))
        assert len(calls) == 4 and all(c.status == "succeeded" for c in calls)
        assert all(c.output_tokens == 8 for c in calls)
        assert all(c.model != "changed-after-admission" and c.input_tokens == 10 for c in calls)
        direct = db.scalar(select(Pipeline).where(Pipeline.name == "direct_llm"))
        assert direct.context["sources"] == []
        assert direct.response["usage"]["output_tokens"] == 8
    for name in items:
        assert system["client"].get(f"{path}/{name}/request").status_code == 409
    login(system["client"], "viewer")
    assert system["client"].get(path).status_code == 403


@pytest.mark.parametrize("problem", ["cancel", "failure"])
def test_local_baseline_failure_preserves_dispatch_without_publication(system, monkeypatch, problem):
    from app.jobs.models import Job
    from app.jobs.queue import claim
    from app.modules.comparisons.processing import process
    from tests.integration.job_readiness import wait_initial
    from tests.integration.support_helpers import fake_retrieval

    monkeypatch.setenv("ASI_GENERATION_MODE", "local_ollama")
    prepare(system)
    path, auth = admit(system)

    def broken(request, context):
        if problem == "cancel":
            assert system["client"].post(path + "/cancel", headers=auth).status_code == 200
            return answer(request, context)
        raise TimeoutError("Synthetic provider timeout")

    monkeypatch.setattr(local_execution, "generate", broken)
    wait_initial(system, "comparison_prepare")
    with Session(system["engine"], expire_on_commit=False) as db, db.begin():
        for queued in db.scalars(select(Job).where(Job.kind == "support_run")):
            queued.priority = 100
        job = claim(db)
        assert job.kind == "comparison_prepare"
    from fastapi import HTTPException

    with pytest.raises(HTTPException if problem == "cancel" else TimeoutError) as caught:
        process(system["engine"], job, retrieval=fake_retrieval)
    if problem == "cancel":
        assert caught.value.status_code == 409 and caught.value.detail == "Comparison was cancelled"
    with Session(system["engine"]) as db:
        call = db.scalar(select(ModelCall).where(ModelCall.operation == "generate"))
        assert call.status == ("succeeded" if problem == "cancel" else "failed")
        item = db.scalar(select(Pipeline).where(Pipeline.job_id == job.id))
        assert item.request is not None and item.response is None
