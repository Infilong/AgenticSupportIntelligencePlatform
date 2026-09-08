import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.ai import AIRun
from app.models.budget import WorkspaceBudgetPolicy
from app.models.evaluation import EvaluationRun
from app.models.reservation import ModelCallReservation
from app.services.model_provider import MockModelProvider
from tests.test_evaluations import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("mode", ["direct_llm", "vector_rag"])
@pytest.mark.parametrize("field,value,reason", [
    ("monthly_token_budget", 1, "monthly_token_budget_exceeded"),
    ("monthly_cost_budget", 0.000000001, "monthly_cost_budget_exceeded"),
    ("per_run_token_budget", 1, "token_budget_exceeded"),
    ("per_run_cost_budget", 0.000000001, "cost_budget_exceeded"),
])
def test_baseline_limit_denies_before_model_dispatch(
    client, db_session, monkeypatch, mode, field, value, reason,
):
    register(client, "budget-evaluation@example.test")
    token = login(client, "budget-evaluation@example.test")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    base = f"/api/v1/workspaces/{workspace_id}"
    uploaded = client.post(base + "/knowledge-documents", headers=auth_headers(token), json={
        "title": "Refund policy", "language": "en", "content_type": "text/plain",
        "content": "Refunds are available within 7 days of purchase.",
    })
    assert uploaded.status_code == 201
    policy = db_session.scalar(select(WorkspaceBudgetPolicy).where(
        WorkspaceBudgetPolicy.workspace_id == workspace_id))
    if policy is None:
        policy = WorkspaceBudgetPolicy(workspace_id=workspace_id)
        db_session.add(policy)
    setattr(policy, field, value)
    db_session.commit()
    calls = []
    original = MockModelProvider.complete

    def observed(self, **kwargs):
        calls.append(kwargs["purpose"])
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", observed)
    response = client.post(base + "/evaluations", headers=auth_headers(token), json={
        "name": "Budget denial", "modes": [mode],
        "jsonl_cases": json.dumps({"id": "case", "language": "en",
                                   "input_message": "Refunds within 7 days?"}),
    })
    assert response.status_code == 201
    assert calls == []
    result = response.json()["results"][0]
    assert result["actual_route"] == "error"
    assert result["error_message"] == reason
    assert result["prompt_tokens"] == 0
    assert result["answer"] is None
    assert db_session.scalar(select(AIRun).where(AIRun.workspace_id == workspace_id)) is None
    reservation = db_session.scalar(select(ModelCallReservation))
    assert reservation.status == "denied"
    assert str(reservation.evaluation_run_id) == response.json()["run"]["id"]
    assert reservation.graph_run_id is None


@pytest.mark.parametrize("expiry_hours", [-1, 1])
def test_baseline_cases_share_allowance_and_active_reservation_blocks_delete(
    client, db_session, expiry_hours,
):
    register(client, "cumulative-evaluation@example.test")
    token = login(client, "cumulative-evaluation@example.test")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    base = f"/api/v1/workspaces/{workspace_id}"
    db_session.add(WorkspaceBudgetPolicy(workspace_id=workspace_id, per_run_token_budget=200))
    db_session.commit()
    response = client.post(base + "/evaluations", headers=auth_headers(token), json={
        "name": "Cumulative", "modes": ["direct_llm"],
        "jsonl_cases": "\n".join(json.dumps({"id": str(i), "language": "en",
                                             "input_message": "word " * 100}) for i in range(3)),
    })
    assert response.status_code == 201
    results = response.json()["results"]
    assert [result["actual_route"] for result in results] == ["finalize", "error", "error"]
    assert all(result["error_message"] == "token_budget_exceeded" for result in results[1:])
    reservations = db_session.scalars(select(ModelCallReservation)).all()
    assert sorted(row.status for row in reservations) == ["consumed", "denied", "denied"]
    assert len(db_session.scalars(select(AIRun)).all()) == 1
    consumed = next(row for row in reservations if row.status == "consumed")
    evaluation_id = UUID(response.json()["run"]["id"])
    evaluation = db_session.get(EvaluationRun, evaluation_id)
    evaluation.archived_at = datetime.now(UTC)
    # Recreate an unresolved reservation to verify that deletion cannot free live allowance.
    consumed.status = "reserved"
    consumed.expires_at = datetime.now(UTC) + timedelta(hours=expiry_hours)
    db_session.commit()
    denied = client.delete(f"{base}/evaluations/{evaluation_id}/permanent",
                           headers=auth_headers(token))
    assert denied.status_code == 409
    assert denied.json()["detail"]["code"] == "evaluation_reservation_active"
    assert db_session.get(EvaluationRun, evaluation_id) is not None
    consumed.status = "consumed"
    db_session.commit()
    assert client.delete(f"{base}/evaluations/{evaluation_id}/permanent",
                         headers=auth_headers(token)).status_code == 204
