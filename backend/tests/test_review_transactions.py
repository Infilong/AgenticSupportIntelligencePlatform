"""Opt-in PostgreSQL tests: RUN_POSTGRES_TESTS=1, using an isolated random schema."""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.models.agent import AgentConfig, Checkpoint, GraphRun, GraphRunStatus
from app.models.audit import AuditLog
from app.models.review import HumanReview, ReviewDecision
from app.models.user import User
from app.models.workspace import Workspace
from app.services.human_review_service import (
    HumanReviewAlreadyResolvedError,
    HumanReviewAssignmentConflictError,
    HumanReviewService,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires isolated PostgreSQL verification"
)


@pytest.fixture
def review_database():
    url = get_settings().database_url
    assert url.startswith("postgresql"), "PostgreSQL verification requires PostgreSQL"
    schema = "review_test_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={
        "options": f"-csearch_path={schema},public -clock_timeout=5000"
    })
    try:
        Base.metadata.create_all(engine, checkfirst=False)
        with Session(engine) as db:
            users = [User(email=f"reviewer{i}@example.test", password_hash="unused",
                          display_name=f"Reviewer {i}") for i in range(2)]
            db.add_all(users)
            db.flush()
            workspace = Workspace(name="Concurrency", created_by_user_id=users[0].id)
            db.add(workspace)
            db.flush()
            agent = AgentConfig(workspace_id=workspace.id, name="Review test")
            db.add(agent)
            db.flush()
            run = GraphRun(workspace_id=workspace.id, agent_config_id=agent.id,
                           user_id=users[0].id, input_message="Refund?", language="en",
                           status=GraphRunStatus.needs_human_review, route_decision="human_review")
            db.add(run)
            db.flush()
            review = HumanReview(workspace_id=workspace.id, graph_run_id=run.id,
                                 reason="confidence_threshold", proposed_answer="Verified policy",
                                 reviewer_decision=ReviewDecision.pending)
            db.add(review)
            db.commit()
            ids = (workspace.id, review.id, [user.id for user in users], run.id)
        yield engine, ids
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def mutate(db, ids, operation, user_index=0):
    workspace_id, review_id, user_ids, _ = ids
    service = HumanReviewService(db)
    args = dict(workspace_id=workspace_id, review_id=review_id,
                reviewer=db.get(User, user_ids[user_index]))
    if operation == "resolve":
        return service.resolve(**args, decision=ReviewDecision.approved,
                               edited_answer=None, comments="Verified")
    return getattr(service, operation)(**args)


@pytest.mark.parametrize("first_operation,second_operation", [
    ("claim", "claim"), ("claim", "release"), ("resolve", "resolve"),
])
def test_competing_transitions_have_one_winner(review_database, first_operation, second_operation):
    engine, ids = review_database
    first_ready, release_first = Event(), Event()
    second_ready, release_second = Event(), Event()
    second_pid = []

    def worker(first):
        with Session(engine, autoflush=False) as db:
            if not first:
                second_pid.append(db.scalar(text("select pg_backend_pid()")))

            def pause_before_commit(session):
                (first_ready if first else second_ready).set()
                assert (release_first if first else release_second).wait(10), "commit wait expired"

            event.listen(db, "before_commit", pause_before_commit)
            try:
                mutate(db, ids, first_operation if first else second_operation,
                       user_index=0 if first or second_operation == "resolve" else 1)
                return "ok"
            except (HumanReviewAssignmentConflictError, HumanReviewAlreadyResolvedError) as exc:
                db.rollback()
                return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(worker, True)
        try:
            assert first_ready.wait(10), "first mutation did not reach commit"
            second = executor.submit(worker, False)
            deadline = time.monotonic() + 10
            observed = False
            while time.monotonic() < deadline:
                # Old code reaches its own commit; fixed code waits on the first row lock.
                with engine.connect() as connection:
                    blocked = second_pid and connection.scalar(text(
                        "select wait_event_type = 'Lock' from pg_stat_activity where pid = :pid"
                    ), {"pid": second_pid[0]})
                if second_ready.is_set() or blocked:
                    observed = True
                    break
                time.sleep(0.02)
            assert observed, "second mutation did not overlap the first"
            release_first.set()
            assert first.result(timeout=10) == "ok"
            release_second.set()
            expected = ("HumanReviewAlreadyResolvedError" if first_operation == "resolve"
                        else "HumanReviewAssignmentConflictError")
            assert second.result(timeout=10) == expected
        finally:
            release_first.set()
            release_second.set()
    with Session(engine) as db:
        review = db.get(HumanReview, ids[1])
        assert review.reviewer_id == ids[2][0]
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 1
        checkpoints = db.scalar(select(func.count()).select_from(Checkpoint))
        assert checkpoints == (1 if first_operation == "resolve" else 0)


def test_audit_failure_rolls_back_review_run_and_checkpoint(review_database):
    engine, ids = review_database
    with Session(engine, autoflush=False) as db:
        def reject_audit(mapper, connection, target):
            raise RuntimeError("injected audit storage failure")

        event.listen(AuditLog, "before_insert", reject_audit)
        try:
            with pytest.raises(RuntimeError, match="injected audit"):
                mutate(db, ids, "resolve")
            db.rollback()
        finally:
            event.remove(AuditLog, "before_insert", reject_audit)
    with Session(engine) as db:
        assert db.get(HumanReview, ids[1]).reviewer_decision == ReviewDecision.pending
        assert db.get(GraphRun, ids[3]).status == GraphRunStatus.needs_human_review
        assert db.scalar(select(func.count()).select_from(Checkpoint)) == 0
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 0


def test_stale_session_cannot_release_new_assignment(review_database):
    engine, ids = review_database
    with Session(engine, autoflush=False) as stale, Session(engine) as owner:
        cached = stale.get(HumanReview, ids[1])
        assert cached.reviewer_id is None
        mutate(owner, ids, "claim")
        with pytest.raises(HumanReviewAssignmentConflictError):
            mutate(stale, ids, "release", user_index=1)
        stale.rollback()
    with Session(engine) as db:
        assert db.get(HumanReview, ids[1]).reviewer_id == ids[2][0]
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 1
