"""Worker execution, ownership, revocation and active stop on real PostgreSQL."""

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.models.agent import GraphRun, GraphStep
from app.models.task import TaskExecution
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.execution_ownership import ExecutionBusy
from app.services.support_agent_graph import SupportAgentGraphRunner
from app.services.task_admission import admit_task
from app.services.task_control import request_stop
from app.services.task_worker import execute_task

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


def queued(engine, ids):
    with Session(engine) as db:
        template = db.get(GraphRun, ids[3])
        db.add(WorkspaceMember(workspace_id=ids[0], user_id=ids[2][0], role=WorkspaceRole.owner))
        db.commit()
        _, run = admit_task(db, workspace_id=ids[0], agent_id=template.agent_config_id,
            user_id=ids[2][0], message="What is the refund policy?", request_key="worker-test")
        return run.id


def test_worker_executes_snapshot_to_review_and_does_not_replay(review_database):
    engine, ids = review_database
    run_id = queued(engine, ids)
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "needs_human_review"
    with Session(engine) as db:
        before = list(db.scalars(select(GraphStep.id).where(GraphStep.graph_run_id == run_id)))
        assert len(before) >= 6
        assert db.get(TaskExecution, run_id).started_at is not None
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "needs_human_review"
    with Session(engine) as db:
        assert list(db.scalars(select(GraphStep.id).where(
            GraphStep.graph_run_id == run_id))) == before


def test_active_stop_prevents_later_steps_and_excludes_second_worker(review_database, monkeypatch):
    engine, ids = review_database
    run_id = queued(engine, ids)
    entered, release = Event(), Event()
    original = SupportAgentGraphRunner.classify_intent

    def pause(runner, state):
        result = original(runner, state)
        entered.set()
        assert release.wait(10)
        return result

    monkeypatch.setattr(SupportAgentGraphRunner, "classify_intent", pause)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(execute_task, engine, workspace_id=ids[0], run_id=run_id)
        try:
            assert entered.wait(10)
            with pytest.raises(ExecutionBusy):
                execute_task(engine, workspace_id=ids[0], run_id=run_id)
            with Session(engine) as db:
                run = request_stop(db, workspace_id=ids[0], run_id=run_id, user_id=ids[2][0])
                assert run.status == "stopping"
                assert run.completed_at is None
        finally:
            release.set()
        assert future.result(timeout=10) == "stopped"
    with Session(engine) as db:
        run = db.get(GraphRun, run_id)
        assert run.final_answer is None
        assert run.completed_at is not None
        assert set(db.scalars(select(GraphStep.step_name).where(
            GraphStep.graph_run_id == run_id))) == {
            "detect_language", "classify_intent"}


@pytest.mark.parametrize("failure", ["permission", "steps", "interrupted"])
def test_worker_limits_and_interruption_do_not_restart_work(review_database, failure):
    engine, ids = review_database
    run_id = queued(engine, ids)
    with Session(engine) as db:
        if failure == "permission":
            db.scalar(select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == ids[0])).role = (
                WorkspaceRole.viewer)
        elif failure == "steps":
            db.get(TaskExecution, run_id).max_steps = 1
        else:
            db.get(GraphRun, run_id).status = "running"
        db.commit()
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "failed"
    with Session(engine) as db:
        expected = {"permission": "execution_permission_revoked", "steps": "execution_step_limit",
                    "interrupted": "worker_interrupted"}[failure]
        assert db.get(TaskExecution, run_id).error_code == expected
        names = list(db.scalars(select(GraphStep.step_name).where(
            GraphStep.graph_run_id == run_id)))
        assert names == (["detect_language"] if failure == "steps" else [])


def test_worker_time_limit_stops_before_next_model_call(review_database, monkeypatch):
    engine, ids = review_database
    run_id = queued(engine, ids)
    original = SupportAgentGraphRunner.detect_language

    def expire(runner, state):
        result = original(runner, state)
        runner.db.get(TaskExecution, run_id).started_at = datetime.now(UTC) - timedelta(seconds=121)
        runner.db.commit()
        return result

    monkeypatch.setattr(SupportAgentGraphRunner, "detect_language", expire)
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "failed"
    with Session(engine) as db:
        assert db.get(TaskExecution, run_id).error_code == "execution_time_limit"
        assert list(db.scalars(select(GraphStep.step_name).where(
            GraphStep.graph_run_id == run_id))) == ["detect_language"]


def test_worker_records_and_propagates_node_failure(review_database, monkeypatch):
    engine, ids = review_database
    run_id = queued(engine, ids)

    def fail(runner, state):
        raise RuntimeError("synthetic node failure")

    monkeypatch.setattr(SupportAgentGraphRunner, "classify_intent", fail)
    with pytest.raises(RuntimeError, match="synthetic node failure"):
        execute_task(engine, workspace_id=ids[0], run_id=run_id)
    with Session(engine) as db:
        assert db.get(GraphRun, run_id).status == "failed"
        assert db.get(TaskExecution, run_id).error_code == "worker_execution_failed"
