"""Real row-lock proof for duplicate approval and approval versus stopping."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database
from test_task_worker_postgres import queued

from app.models.agent import AgentConfig, GraphRun
from app.models.audit import AuditLog
from app.models.task import TaskExecution
from app.models.task_action import TaskNote
from app.schemas.task_action import TaskActionInput
from app.services.task_actions import TaskActionError, resolve_proposal, stage_proposal
from app.services.task_control import request_stop

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


@pytest.mark.parametrize("race", ["duplicate", "stop"])
def test_concurrent_resolution_has_one_side_effect(review_database, race):
    engine, ids = review_database
    run_id = queued(engine, ids)
    with Session(engine) as db:
        run = db.get(GraphRun, run_id)
        run.status = "running"
        settings = {"allowed_actions": ["add_note"]}
        db.get(AgentConfig, run.agent_config_id).settings_json = json.dumps(settings)
        db.get(TaskExecution, run_id).agent_snapshot_json = json.dumps({"settings": settings})
        proposal = stage_proposal(db, run=run, inputs=TaskActionInput(
            action="add_note", value="Approved internal note"))
        run.status = "needs_human_review"
        db.commit()
        args = dict(workspace_id=ids[0], proposal_id=proposal.id, reviewer_id=ids[2][0],
                    expected_hash=proposal.proposal_hash, approve=True)
    barrier = Barrier(2)

    def resolve():
        with Session(engine) as db:
            barrier.wait(timeout=10)
            try:
                return resolve_proposal(db, **args).status
            except TaskActionError:
                db.rollback()
                return "denied"

    def stop():
        with Session(engine) as db:
            barrier.wait(timeout=10)
            return request_stop(db, workspace_id=ids[0], run_id=run_id,
                                user_id=ids[2][0]).status

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(resolve)
        second = pool.submit(resolve if race == "duplicate" else stop)
        results = first.result(timeout=15), second.result(timeout=15)
    with Session(engine) as db:
        notes = db.scalar(select(func.count()).select_from(TaskNote))
        audits = db.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "task_action.applied"))
        if race == "duplicate":
            assert results == ("applied", "applied")
            assert notes == audits == 1
        else:
            assert results in {("applied", "stopped"), ("denied", "stopped")}
            assert notes == audits == (results[0] == "applied")
            assert db.get(GraphRun, run_id).status == "stopped"
            # After confirmed stop no new side effect can occur, including a lost-response retry.
            try:
                resolve_proposal(db, **args)
            except TaskActionError:
                db.rollback()
            assert db.scalar(select(func.count()).select_from(TaskNote)) == notes
