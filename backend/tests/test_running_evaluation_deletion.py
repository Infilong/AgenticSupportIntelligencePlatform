import json
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationMode, EvaluationRun, EvaluationRunStatus
from app.models.reservation import ModelCallReservation
from app.models.user import User
from app.services.evaluation_runner import EvaluationRunner
from tests.test_evaluation_authorization_boundary import snapshot
from tests.test_review_transactions import review_database as review_database
from tests.test_workflow_authorization import protected_workflow as protected_workflow


def test_running_evaluation_delete_returns_conflict(client, db_session, protected_workflow):
    data = protected_workflow
    path = f"{data['base']}/evaluations/{data['evaluation']}"
    run = db_session.scalar(select(EvaluationRun))
    run.status = EvaluationRunStatus.running
    db_session.commit()
    assert client.delete(path, headers=data["owner"]).status_code == 204
    before = snapshot(db_session)
    response = client.delete(path + "/permanent", headers=data["owner"])
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "evaluation_running"
    assert snapshot(db_session) == before


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_evaluation_cannot_be_deleted_between_model_calls(review_database, monkeypatch):
    engine, ids = review_database
    paused, release = Event(), Event()
    original = EvaluationRunner._run_case
    observed_ids = []

    def pause_after_case(self, **kwargs):
        result = original(self, **kwargs)
        observed_ids.append(kwargs["run_id"])
        paused.set()
        assert release.wait(15), "evaluation completion gate expired"
        return result

    monkeypatch.setattr(EvaluationRunner, "_run_case", pause_after_case)

    def evaluate():
        with Session(engine) as db:
            return EvaluationRunner(db).run_from_jsonl(
                workspace_id=ids[0], name="Running evaluation", agent_id=None,
                modes=[EvaluationMode.direct_llm], current_user=db.get(User, ids[2][0]),
                jsonl_cases=json.dumps({"id": "case", "language": "en",
                                       "input_message": "Refund?"}),
            ).id

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(evaluate)
        try:
            assert paused.wait(15)
            with Session(engine) as db:
                run_id, = observed_ids
                reservations = db.scalars(select(ModelCallReservation)).all()
                assert reservations and all(row.status != "reserved" for row in reservations)
                service = EvaluationRunner(db)
                args = {"workspace_id": ids[0], "run_id": run_id, "actor_user_id": ids[2][0]}
                service.archive_run(**args)
                before = snapshot(db)
                with pytest.raises(ValueError, match="still running"):
                    service.delete_archived_run(**args)
                assert snapshot(db) == before
        finally:
            release.set()
        assert future.result(timeout=15) == observed_ids[0]
    with Session(engine) as db:
        run = db.get(EvaluationRun, observed_ids[0])
        assert run.status == EvaluationRunStatus.completed
        assert run.archived_at is not None and run.results and run.metrics
        EvaluationRunner(db).delete_archived_run(
            workspace_id=ids[0], run_id=run.id, actor_user_id=ids[2][0])
