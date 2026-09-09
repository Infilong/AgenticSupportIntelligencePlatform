import multiprocessing
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.modules.knowledge.recovery import RetrievalOwner, RetrievalOwnershipLost, reconcile
from app.modules.knowledge.retrieval import retrieve
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.usage.models import ModelCall
from app.providers.local_embeddings import EmbeddingBatch


class BlockedEmbedding:
    def __init__(self, started, release, fail=False):
        self.started, self.release, self.fail = started, release, fail

    def encode_batch(self, texts, kind):
        self.started.set()
        if not self.release.wait(15):
            raise TimeoutError("Test did not release inference")
        if self.fail:
            raise ValueError("Injected late provider failure")
        return EmbeddingBatch([[1.0] + [0.0] * 383], 5, 1.0)


def records(system):
    with Session(system["engine"]) as db:
        trace = db.scalar(select(RetrievalTrace))
        calls = list(db.scalars(select(ModelCall)))
        return trace, calls


@pytest.mark.parametrize("fail", [False, True])
def test_lost_owner_cannot_overwrite_uncertainty_or_dispatch_more_calls(system, monkeypatch, fail):
    import app.modules.knowledge.retrieval as module

    owners = []

    def capture(engine):
        owner = RetrievalOwner(engine)
        owners.append(owner)
        return owner

    monkeypatch.setattr(module, "RetrievalOwner", capture)
    started, release = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            retrieve,
            system["engine"],
            system["workspace"],
            system["users"]["admin"].id,
            "refund deadline",
            provider=BlockedEmbedding(started, release, fail),
        )
        try:
            assert started.wait(10)
            assert reconcile(system["engine"])[1] == 0  # Live ownership is not abandoned.
            with system["engine"].begin() as db:
                assert db.scalar(
                    text("SELECT pg_terminate_backend(:pid)"), {"pid": owners[0].connection.info.backend_pid}
                )
            assert reconcile(system["engine"])[1] == 1
        finally:
            release.set()
        with pytest.raises(RetrievalOwnershipLost):
            future.result(timeout=10)
    trace, calls = records(system)
    assert trace.status == "uncertain" and trace.error_code == "retrieval_ownership_lost"
    assert trace.results == [] and trace.duration_ms is None
    assert len(calls) == 1 and calls[0].status == "uncertain"
    assert calls[0].input_tokens is None and calls[0].api_cost_usd is None


def test_live_owner_finishes_normally_after_recovery_sweep(system):
    started, release = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(
            retrieve,
            system["engine"],
            system["workspace"],
            system["users"]["admin"].id,
            "refund deadline",
            provider=BlockedEmbedding(started, release),
        )
        try:
            assert started.wait(10)
            assert reconcile(system["engine"])[1] == 0
        finally:
            release.set()
        assert future.result(timeout=10)["status"] == "no_sources"
    trace, calls = records(system)
    assert trace.status == "succeeded" and calls[0].status == "succeeded"
    assert calls[0].input_tokens == 5 and calls[0].api_cost_usd == 0


def test_fair_cursor_finds_abandoned_trace_behind_live_owner_and_preserves_finished_calls(system):
    engine = system["engine"]
    owner = RetrievalOwner(engine)
    owner.trace_id = uuid.UUID(int=1)
    with owner:
        abandoned_id = uuid.UUID(int=2)
        with Session(engine) as db, db.begin():
            for trace_id in (owner.trace_id, abandoned_id):
                db.add(
                    RetrievalTrace(
                        id=trace_id,
                        workspace_id=system["workspace"],
                        actor_id=system["users"]["admin"].id,
                        query="synthetic",
                    )
                )
            db.flush()
            db.add(
                ModelCall(
                    workspace_id=system["workspace"],
                    actor_id=system["users"]["admin"].id,
                    retrieval_id=abandoned_id,
                    operation="embed_query",
                    provider="local_cpu",
                    model="test",
                    revision="test",
                    status="succeeded",
                    input_tokens=9,
                    duration_ms=3,
                    api_cost_usd=0,
                )
            )
        cursor, repaired = reconcile(engine, limit=1)
        assert cursor == owner.trace_id and repaired == 0
        cursor, repaired = reconcile(engine, cursor, limit=1)
        assert cursor == abandoned_id and repaired == 1
        assert reconcile(engine, cursor, limit=1) == (None, 0)
        with Session(engine) as db:
            assert db.get(RetrievalTrace, owner.trace_id).status == "started"
            assert db.get(RetrievalTrace, abandoned_id).status == "uncertain"
            call = db.scalar(select(ModelCall))
            assert (call.status, call.input_tokens, call.duration_ms, call.api_cost_usd) == (
                "succeeded",
                9,
                3,
                0,
            )


def killed_retrieval(url, workspace_id, actor_id, pipe):
    """Real spawned process; fake only model latency, not database/ownership/retrieval code."""
    from app.modules.identity import models as identity_models  # noqa: F401

    class Model:
        def encode_batch(self, texts, kind):
            pipe.send("inference_started")
            pipe.recv()
            raise AssertionError("Parent should terminate this process")

    engine = create_engine(url, hide_parameters=True)
    try:
        retrieve(engine, workspace_id, actor_id, "synthetic crash test", provider=Model())
    finally:
        engine.dispose()


def test_real_process_kill_releases_ownership_and_concurrent_sweeps_converge(system):
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(
        target=killed_retrieval,
        args=(
            system["engine"].url.render_as_string(hide_password=False),
            system["workspace"],
            system["users"]["admin"].id,
            child,
        ),
    )
    process.start()
    try:
        assert parent.poll(20), "Child did not reach persisted model dispatch"
        assert parent.recv() == "inference_started"
        assert reconcile(system["engine"])[1] == 0
        process.terminate()
        process.join(10)
        assert not process.is_alive() and process.exitcode != 0
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: reconcile(system["engine"]), range(2)))
        assert sum(count for _, count in results) == 1
        trace, calls = records(system)
        assert trace.status == "uncertain" and len(calls) == 1 and calls[0].status == "uncertain"
        assert calls[0].api_cost_usd is None and calls[0].duration_ms is None
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        parent.close()
        child.close()
