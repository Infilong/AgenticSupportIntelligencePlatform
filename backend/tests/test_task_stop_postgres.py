"""Stop versus review publication under real PostgreSQL row locks."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_review_transactions import mutate
from test_review_transactions import review_database as review_database

from app.models.agent import GraphRun
from app.models.review import HumanReview
from app.models.task import SupportTask, TaskExecution
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.review_transaction import HumanReviewAlreadyResolvedError
from app.services.task_control import TaskControlError, request_stop


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_review_and_stop_cannot_both_publish(review_database):
    engine, ids = review_database
    workspace_id, review_id, users, run_id = ids
    with Session(engine) as db:
        run = db.get(GraphRun, run_id)
        db.add(WorkspaceMember(workspace_id=workspace_id, user_id=users[0],
                               role=WorkspaceRole.owner))
        task = SupportTask(workspace_id=workspace_id, created_by_user_id=users[0],
            agent_config_id=run.agent_config_id, request_key="stop-review", request_hash="a" * 64,
            input_message=run.input_message)
        db.add(task)
        db.flush()
        db.add(TaskExecution(workspace_id=workspace_id, task_id=task.id, graph_run_id=run_id,
                             initial_state_json="{}", agent_snapshot_json="{}"))
        db.commit()
    barrier = Barrier(2)

    def stop():
        with Session(engine) as db:
            barrier.wait(timeout=10)
            try:
                request_stop(db, workspace_id=workspace_id, run_id=run_id, user_id=users[0])
                return "stopped"
            except TaskControlError:
                db.rollback()
                return "already_completed"

    def resolve():
        with Session(engine) as db:
            barrier.wait(timeout=10)
            try:
                mutate(db, ids, "resolve")
                return "completed"
            except HumanReviewAlreadyResolvedError:
                db.rollback()
                return "already_stopped"

    with ThreadPoolExecutor(max_workers=2) as pool:
        stopping, resolving = pool.submit(stop), pool.submit(resolve)
        results = stopping.result(timeout=15), resolving.result(timeout=15)
    assert results in {("stopped", "already_stopped"), ("already_completed", "completed")}
    with Session(engine) as db:
        run = db.get(GraphRun, run_id)
        review = db.scalar(select(HumanReview).where(HumanReview.id == review_id))
        if results[0] == "stopped":
            assert run.status == "stopped"
            assert run.final_answer is None
            assert review.reviewer_decision == "rejected"
        else:
            assert run.status == "completed"
            assert run.final_answer == "Verified policy"
            assert review.reviewer_decision == "approved"
