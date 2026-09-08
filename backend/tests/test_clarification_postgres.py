"""A durable worker parks incomplete input without review, billing or replay."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.models.agent import GraphRun, GraphStep
from app.models.ai import AIRun
from app.models.review import HumanReview
from app.models.task import TaskExecution
from app.models.workspace import WorkspaceMember
from app.services.task_admission import admit_task
from app.services.task_control import request_stop
from app.services.task_worker import execute_task

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


@pytest.mark.parametrize("language, fragment", [
    ("en", "clarify"), ("ja", "ご質問"), ("zh", "问题"),
])
def test_worker_persists_clarification_without_replaying(review_database, language, fragment):
    engine, ids = review_database
    with Session(engine) as db:
        template = db.get(GraphRun, ids[3])
        db.add(WorkspaceMember(workspace_id=ids[0], user_id=ids[2][0], role="owner"))
        db.commit()
        _, run = admit_task(db, workspace_id=ids[0], user_id=ids[2][0],
            agent_id=template.agent_config_id, message="?", request_key="clarification",
            language=language)
        run_id = run.id
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "awaiting_clarification"
    assert execute_task(engine, workspace_id=ids[0], run_id=run_id) == "awaiting_clarification"
    with Session(engine) as db:
        run = db.get(GraphRun, run_id)
        assert fragment in run.final_answer
        assert run.language == language
        assert db.scalar(select(func.count()).select_from(GraphStep).where(
            GraphStep.graph_run_id == run_id)) == 1
        assert db.scalar(select(func.count()).select_from(AIRun).where(
            AIRun.graph_run_id == run_id)) == 0
        assert db.scalar(select(func.count()).select_from(HumanReview).where(
            HumanReview.graph_run_id == run_id)) == 0
        stopped = request_stop(db, workspace_id=ids[0], run_id=run_id, user_id=ids[2][0])
        assert stopped.status == "stopped"


def test_concurrent_clarification_creates_one_attempt(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        template = db.get(GraphRun, ids[3])
        agent_id = template.agent_config_id
        db.add(WorkspaceMember(workspace_id=ids[0], user_id=ids[2][0], role="owner"))
        db.commit()
        task, run = admit_task(db, workspace_id=ids[0], user_id=ids[2][0],
            agent_id=agent_id, message="w", request_key="original")
        task_id, parent_id = task.id, run.id
    execute_task(engine, workspace_id=ids[0], run_id=parent_id)
    barrier = Barrier(2)

    def reply(_):
        with Session(engine) as db:
            barrier.wait(timeout=10)
            return admit_task(db, workspace_id=ids[0], user_id=ids[2][0],
                agent_id=agent_id, message="Refund policy?", request_key="same-reply",
                parent_run_id=parent_id, clarification_reply="Refund policy?")[1].id

    with ThreadPoolExecutor(max_workers=2) as pool:
        children = list(pool.map(reply, range(2)))
    assert children[0] == children[1]
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(TaskExecution).where(
            TaskExecution.task_id == task_id)) == 2
        assert db.get(GraphRun, parent_id).route_decision == "clarification_received"
