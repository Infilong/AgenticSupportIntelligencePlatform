import json

import pytest
from sqlalchemy import event, select

from app.models.ai import AIRun
from app.models.evaluation import EvaluationMetric, EvaluationRun
from app.models.reservation import ModelCallReservation
from app.services.evaluation_runner import EvaluationRunner
from tests.test_evaluations import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("failure", ["case", "metrics", "failure_record"])
def test_unexpected_evaluation_failure_is_terminal_with_usage(
    client, db_session, monkeypatch, caplog, failure,
):
    register(client, "terminal-evaluation@example.test")
    token = login(client, "terminal-evaluation@example.test")
    workspace = create_workspace(client, token)
    primary = RuntimeError("private-synthetic-evaluation-error")
    original = EvaluationRunner._run_case

    def case(self, **kwargs):
        result = original(self, **kwargs)
        if failure == "case":
            raise primary
        return result

    def metrics(db, context, instances):
        if failure != "case" and any(isinstance(row, EvaluationMetric) for row in db.new):
            raise primary
        if failure == "failure_record" and any(
            isinstance(row, EvaluationRun) and row.status == "failed" for row in db.dirty
        ):
            raise ValueError("private-failure-record-error")

    monkeypatch.setattr(EvaluationRunner, "_run_case", case)
    event.listen(db_session, "before_flush", metrics)
    try:
        with pytest.raises(RuntimeError) as raised:
            client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                        headers=auth_headers(token), json={
                "name": "Terminal failure", "modes": ["direct_llm"],
                "jsonl_cases": json.dumps({"id": "case", "language": "en",
                                           "input_message": "Refund?"}),
            })
        assert raised.value is primary
    finally:
        event.remove(db_session, "before_flush", metrics)
        db_session.rollback()
    run = db_session.scalar(select(EvaluationRun))
    assert run.status == ("running" if failure == "failure_record" else "failed")
    assert (run.completed_at is not None) == (failure != "failure_record")
    assert run.results
    assert not run.metrics
    ledger = db_session.scalar(select(AIRun))
    reservation = db_session.scalar(select(ModelCallReservation))
    assert ledger and ledger.total_tokens > 0
    assert reservation.status == "consumed" and reservation.ai_run_id == ledger.id
    records = [record.getMessage() for record in caplog.records
               if record.name == "app.services.evaluation_execution"]
    message, = records
    assert "private-" not in message
    diagnostic = json.loads(message)
    assert diagnostic["evaluation_run_id"] == str(run.id)
    assert diagnostic["request_id"]
    assert diagnostic["error_type"] == "RuntimeError"
    assert diagnostic["failure_recorded"] == (failure != "failure_record")
    assert diagnostic["recording_error_type"] == (
        "ValueError" if failure == "failure_record" else None)
