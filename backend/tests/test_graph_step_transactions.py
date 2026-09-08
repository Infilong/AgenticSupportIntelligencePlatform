"""Per-run sequence allocation and rollback on real PostgreSQL."""
# ruff: noqa: F811

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from test_review_transactions import review_database  # noqa: F401

from app.models.agent import GraphStep
from app.services.graph_step_ordering import persist_step, step_order

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


def new_step(ids, index=0):
    return GraphStep(workspace_id=ids[0], graph_run_id=ids[3], step_name="test",
                     input_json="{}", output_json="{}", status="succeeded", latency_ms=1,
                     created_at=datetime(2026, 9, 8, tzinfo=UTC) - timedelta(seconds=index))


def test_concurrent_steps_have_unique_order_and_matching_parents(review_database):
    engine, ids = review_database
    ready = Barrier(2)

    def worker():
        with Session(engine) as db:
            for index in range(6):
                ready.wait(timeout=10)
                persist_step(db, new_step(ids, index))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        for future in futures:
            future.result(timeout=30)
    with Session(engine) as db:
        steps = list(db.scalars(select(GraphStep).order_by(*step_order())))
        assert [step.sequence for step in steps] == list(range(1, 13))
        assert steps[0].parent_span_id is None
        for previous, current in zip(steps, steps[1:], strict=False):
            assert current.parent_span_id == previous.span_id


def test_failure_releases_sequence_and_wrong_workspace_cannot_append(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        first = new_step(ids)
        persist_step(db, first)

        def fail_flush(session, context, instances):
            raise RuntimeError("injected persistence failure")

        event.listen(db, "before_flush", fail_flush)
        try:
            with pytest.raises(RuntimeError, match="injected persistence failure"):
                persist_step(db, new_step(ids))
        finally:
            event.remove(db, "before_flush", fail_flush)
        wrong_scope = new_step(ids)
        wrong_scope.workspace_id = uuid4()
        with pytest.raises(ValueError, match="unavailable"):
            persist_step(db, wrong_scope)
        second = new_step(ids)
        persist_step(db, second)
        assert second.sequence == 2
        assert second.parent_span_id == first.span_id
        for invalid_sequence in (0, -1, 2):
            invalid = new_step(ids)
            invalid.sequence = invalid_sequence
            db.add(invalid)
            with pytest.raises(IntegrityError):
                db.commit()
            db.rollback()


def test_legacy_history_is_explicitly_unknown_and_readable(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        legacy = new_step(ids)
        db.add(legacy)
        db.commit()
        current = new_step(ids, 1)
        persist_step(db, current)
        rows = list(db.scalars(select(GraphStep).order_by(*step_order())))
        assert [step.sequence for step in rows] == [None, 1]
        assert current.parent_span_id == legacy.span_id
