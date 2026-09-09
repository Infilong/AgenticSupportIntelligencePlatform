import threading
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.modules.knowledge.recovery import RetrievalOwner, RetrievalOwnershipLost, reconcile
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.usage.models import ModelCall
from app.providers.local_reranker import RerankBatch
from tests.integration.conftest import login
from tests.integration.test_knowledge import add_version
from tests.integration.test_retrieval import ingest_checked, search


@pytest.mark.parametrize("fail", [False, True])
def test_late_rerank_outcome_cannot_overwrite_uncertainty(system, monkeypatch, fail):
    import app.modules.knowledge.retrieval as module

    ingest_checked(system, add_version(system))
    owners = []

    def capture(engine):
        owner = RetrievalOwner(engine)
        owners.append(owner)
        return owner

    monkeypatch.setattr(module, "RetrievalOwner", capture)
    started, release = threading.Event(), threading.Event()

    class Ranking:
        def score(self, query, passages):
            started.set()
            if not release.wait(15):
                raise TimeoutError("Test did not release scoring")
            if fail:
                raise ValueError("Injected late scoring failure")
            return RerankBatch([1.0] * len(passages), 9, 2)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(search, system, ranking_provider=Ranking())
        try:
            assert started.wait(10)
            assert reconcile(system["engine"])[1] == 0
            with system["engine"].begin() as db:
                assert db.scalar(
                    text("SELECT pg_terminate_backend(:pid)"), {"pid": owners[0].connection.info.backend_pid}
                )
            assert reconcile(system["engine"])[1] == 1
        finally:
            release.set()
        with pytest.raises(RetrievalOwnershipLost):
            future.result(timeout=10)
    with Session(system["engine"]) as db:
        trace = db.get(RetrievalTrace, owners[0].trace_id)
        calls = list(db.scalars(select(ModelCall).where(ModelCall.retrieval_id == trace.id)))
        assert trace.status == "uncertain" and trace.results == []
        assert len(calls) == 2
        embed = next(call for call in calls if call.operation == "embed_query")
        rank = next(call for call in calls if call.operation == "rerank")
        assert embed.status == "succeeded" and embed.input_tokens is not None
        assert rank.status == "uncertain" and rank.input_tokens is None and rank.api_cost_usd is None


def test_pretrace_connection_failure_is_retryable_and_api_returns_safe_503(system, monkeypatch):
    import app.modules.knowledge.recovery as module

    headers = login(system["client"], "viewer")

    def unavailable(*args, **kwargs):
        raise psycopg.OperationalError("Synthetic private diagnostic must not reach response")

    monkeypatch.setattr(module.psycopg, "connect", unavailable)
    response = system["client"].post(
        f"/api/workspaces/{system['workspace']}/retrieval", headers=headers, json={"query": "refund deadline"}
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "Search was interrupted. Please retry."}
    with pytest.raises(RetrievalOwnershipLost):
        with RetrievalOwner(system["engine"]):
            pytest.fail("Unavailable owner should not enter")


def test_exception_cleanup_after_owner_loss_cannot_report_a_known_failure(system, monkeypatch):
    import app.modules.knowledge.retrieval as module

    owners = []

    def capture(engine):
        owner = RetrievalOwner(engine)
        owners.append(owner)
        return owner

    def fail_after_disconnect(*args):
        with system["engine"].begin() as db:
            assert db.scalar(
                text("SELECT pg_terminate_backend(:pid)"), {"pid": owners[0].connection.info.backend_pid}
            )
        raise ValueError("Injected candidate failure after ownership loss")

    monkeypatch.setattr(module, "RetrievalOwner", capture)
    monkeypatch.setattr(module, "candidates", fail_after_disconnect)
    with pytest.raises(RetrievalOwnershipLost):
        search(system)
    assert reconcile(system["engine"])[1] == 1
    with Session(system["engine"]) as db:
        trace = db.get(RetrievalTrace, owners[0].trace_id)
        assert trace.status == "uncertain" and trace.error_code == "retrieval_ownership_lost"
        call = db.scalar(select(ModelCall).where(ModelCall.retrieval_id == trace.id))
        assert call.status == "succeeded" and call.input_tokens is not None
