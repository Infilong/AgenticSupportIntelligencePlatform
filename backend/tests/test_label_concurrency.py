import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.models.dataset import ConversationExample, ImportSourceType, Label, LabelSource, LabelType
from app.models.user import User
from app.services.dataset_service import DatasetService

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


@pytest.fixture
def label_data(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        result = DatasetService(db).import_dataset(
            workspace_id=ids[0], dataset_name="Labels", description=None,
            source_type=ImportSourceType.jsonl,
            content=json.dumps({"messages": [{"role": "user", "content": "Refund request"}]}),
        )
        example = db.scalar(select(ConversationExample).where(
            ConversationExample.dataset_id == result.dataset.id,
        ))
        return engine, ids, example.id


def edit(db, ids, example_id, value, actor=0):
    return DatasetService(db).upsert_human_label(
        workspace_id=ids[0], example_id=example_id, label_type=LabelType.intent,
        value=value, current_user=db.get(User, ids[2][actor]),
    )


def test_stale_label_can_restore_value_after_another_edit(label_data):
    engine, ids, example_id = label_data
    with Session(engine) as db:
        label_id = edit(db, ids, example_id, "original").id
    with Session(engine) as stale:
        cached = stale.get(Label, label_id)
        assert cached.value == "original"
        with Session(engine) as other:
            edit(other, ids, example_id, "changed")
        edit(stale, ids, example_id, "original", actor=1)
    with Session(engine) as db:
        label = db.get(Label, label_id)
        assert label.value == "original"
        assert label.created_by_user_id == ids[2][1]


def test_concurrent_first_labels_both_succeed_with_one_row(label_data):
    engine, ids, example_id = label_data
    entered, release, ready = Event(), Event(), Event()
    second_pid = []

    def first():
        with Session(engine) as db:
            def pause(session, context, instances):
                if any(isinstance(row, Label) for row in session.new):
                    entered.set()
                    assert release.wait(15)

            event.listen(db, "before_flush", pause)
            try:
                return edit(db, ids, example_id, "first").id
            finally:
                event.remove(db, "before_flush", pause)

    def second():
        with Session(engine) as db:
            second_pid.append(db.scalar(text("select pg_backend_pid()")))
            ready.set()
            return edit(db, ids, example_id, "second", actor=1).id

    with ThreadPoolExecutor(max_workers=2) as pool:
        initial = pool.submit(first)
        try:
            assert entered.wait(10)
            following = pool.submit(second)
            assert ready.wait(10)
            # Before the repair the second insert can commit while the first has not flushed.
            deadline = time.monotonic() + 3
            with engine.connect() as observer:
                while not following.done() and time.monotonic() < deadline:
                    if observer.scalar(text("select cardinality(pg_blocking_pids(:pid))"),
                                       {"pid": second_pid[0]}):
                        break
                    time.sleep(0.01)
        finally:
            release.set()
        assert initial.result(10) == following.result(10)
    with Session(engine) as db:
        label, = db.scalars(select(Label).where(Label.source == LabelSource.human)).all()
        assert label.value == "second"
        assert label.created_by_user_id == ids[2][1]
