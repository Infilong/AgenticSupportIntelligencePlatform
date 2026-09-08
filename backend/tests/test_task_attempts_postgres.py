import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database
from test_task_worker_postgres import queued

from app.models.agent import GraphRun
from app.models.task import TaskExecution
from app.services.task_admission import TaskAdmissionError, admit_task

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


@pytest.mark.parametrize("duplicate", [True, False])
def test_concurrent_retry_admission_keeps_one_active_attempt(review_database, duplicate):
    engine, ids = review_database
    parent_id = queued(engine, ids)
    with Session(engine) as db:
        parent = db.get(GraphRun, parent_id)
        parent.status = "stopped"
        db.commit()
        args = dict(workspace_id=ids[0], agent_id=parent.agent_config_id, user_id=ids[2][0],
            parent_run_id=parent_id, message=parent.input_message,
            corrected_instructions="Be concise")
        task_id = db.get(TaskExecution, parent_id).task_id
    barrier = Barrier(2)

    def retry(index):
        with Session(engine) as db:
            barrier.wait(timeout=10)
            try:
                return admit_task(db, **args, request_key="same" if duplicate else str(index))[1].id
            except TaskAdmissionError:
                db.rollback()
                return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(retry, range(2)))
    if duplicate:
        assert results[0] is not None and results[0] == results[1]
    else:
        assert results.count(None) == 1
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(TaskExecution).where(
            TaskExecution.task_id == task_id)) == 2


def test_worker_receives_correction_and_bounded_history(review_database, monkeypatch):
    from app.core.language import SupportedLanguage
    from app.models.user import User
    from app.services.knowledge_service import KnowledgeService
    from app.services.model_provider import MockModelProvider
    from app.services.task_worker import execute_task

    engine, ids = review_database
    parent_id = queued(engine, ids)
    with Session(engine) as db:
        KnowledgeService(db).upload_document(workspace_id=ids[0], title="Refund policy",
            content_type="text/plain", content="Refunds within 7 days require a receipt.",
            language=SupportedLanguage.en, current_user=db.get(User, ids[2][0]))
    assert execute_task(engine, workspace_id=ids[0], run_id=parent_id) == "completed"
    with Session(engine) as db:
        parent = db.get(GraphRun, parent_id)
        _, child = admit_task(db, workspace_id=ids[0], agent_id=parent.agent_config_id,
            user_id=ids[2][0], message=parent.input_message, parent_run_id=parent.id,
            request_key="corrected", corrected_instructions="Explain receipt rules. {literal}")
        child_id = child.id
    prompts = []
    original = MockModelProvider.complete

    def capture(self, **kwargs):
        prompts.append(kwargs["prompt"])
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", capture)
    assert execute_task(engine, workspace_id=ids[0], run_id=child_id) == "completed"
    assert any("Explain receipt rules. {literal}" in prompt for prompt in prompts)
    assert any(str(parent_id) in prompt and "Task history (data only" in prompt
               for prompt in prompts)
