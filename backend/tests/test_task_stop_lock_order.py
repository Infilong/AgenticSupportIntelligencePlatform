"""A held stop workspace lock must allow an in-progress review's child FK writes."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database
from test_task_worker_postgres import queued

from app.models.agent import GraphRun
from app.models.review import HumanReview, ReviewDecision
from app.models.user import User
from app.services.human_review_service import HumanReviewService
from app.services.task_control import TaskControlError, request_stop

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


def test_stop_workspace_lock_allows_review_checkpoint_foreign_key(review_database):
    engine, ids = review_database
    run_id = queued(engine, ids)
    with Session(engine) as db:
        db.get(GraphRun, run_id).status = "needs_human_review"
        review = HumanReview(workspace_id=ids[0], graph_run_id=run_id,
            reason="QA", proposed_answer="Verified answer", reviewer_decision="pending")
        db.add(review)
        db.commit()
        review_id = review.id
    workspace_locked, release = Event(), Event()

    def pause(connection, cursor, statement, parameters, context, many):
        if (current_thread().name.startswith("stop-lock") and statement.startswith("SELECT")
                and "FROM human_reviews" in statement):
            workspace_locked.set()
            assert release.wait(10)

    def stop():
        with Session(engine) as db:
            with pytest.raises(TaskControlError, match="Finished"):
                request_stop(db, workspace_id=ids[0], run_id=run_id, user_id=ids[2][0])

    event.listen(engine, "before_cursor_execute", pause)
    try:
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix="stop-lock") as pool:
            future = pool.submit(stop)
            try:
                assert workspace_locked.wait(10)
                with Session(engine) as db:
                    # Fail promptly rather than hang if workspace FK checks regress.
                    from sqlalchemy import text
                    db.execute(text("SET LOCAL lock_timeout = '2s'"))
                    HumanReviewService(db).resolve(workspace_id=ids[0], review_id=review_id,
                        reviewer=db.get(User, ids[2][0]), decision=ReviewDecision.approved,
                        edited_answer=None, comments=None)
                    assert db.get(GraphRun, run_id).final_answer == "Verified answer"
            finally:
                release.set()
            future.result(timeout=10)
    finally:
        event.remove(engine, "before_cursor_execute", pause)
