import json
from uuid import UUID

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.ai import AIRun
from app.models.reservation import ModelCallReservation
from app.services.model_provider import UrllibOpenAIChatTransport
from tests.test_evaluations import auth_headers, create_workspace, login, register


@pytest.mark.parametrize("mode", ["direct_llm", "vector_rag"])
def test_evaluation_usage_overrun_keeps_recorded_cost_and_rejects_answer(
    client, db_session, monkeypatch, mode,
):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-key-never-sent")
    get_settings.cache_clear()
    calls = []

    def overrun(self, **kwargs):
        calls.append(kwargs["prompt"])
        return {"choices": [{"message": {"content": "Unpublishable provider answer."}}],
                "usage": {"prompt_tokens": 4000, "completion_tokens": 100, "total_tokens": 4100}}

    monkeypatch.setattr(UrllibOpenAIChatTransport, "create_chat_completion", overrun)
    register(client, "failure-usage@example.test")
    token = login(client, "failure-usage@example.test")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    base = f"/api/v1/workspaces/{workspace_id}"
    assert client.post(base + "/knowledge-documents", headers=auth_headers(token), json={
        "title": "Refund policy", "language": "en", "content_type": "text/plain",
        "content": "Refunds are available within 7 days of purchase.",
    }).status_code == 201
    assert client.post(base + "/model-configs", headers=auth_headers(token), json={
        "provider": "openai-compatible", "model": "synthetic-usage-model",
        "purpose": f"evaluation_{mode}", "prompt_token_cost_per_1k": 0.01,
        "completion_token_cost_per_1k": 0.02, "max_context_tokens": 8192, "active": True,
    }).status_code == 201
    response = client.post(base + "/evaluations", headers=auth_headers(token), json={
        "name": "Recorded failure usage", "modes": [mode],
        "jsonl_cases": json.dumps({"id": "usage", "language": "en",
                                   "input_message": "Refunds within 7 days?"}),
    })
    assert response.status_code == 201
    assert len(calls) == 1
    result = response.json()["results"][0]
    assert result["actual_route"] == "error"
    assert result["error_message"] == "provider_usage_exceeded_reservation"
    assert result["answer"] is None and result["passed"] is False
    ledger = db_session.scalar(select(AIRun).where(AIRun.workspace_id == workspace_id))
    assert ledger is not None and ledger.prompt_tokens == 4000
    assert result["prompt_tokens"] == ledger.prompt_tokens
    assert result["estimated_cost"] == ledger.estimated_cost > 0
    reservation = db_session.scalar(select(ModelCallReservation))
    assert reservation.ai_run_id == ledger.id and reservation.status == "consumed"
    metrics = {item["metric_name"]: item["metric_value"] for item in response.json()["metrics"]}
    assert metrics["average_prompt_tokens"] == 4000
    assert metrics["estimated_cost_per_run"] == round(ledger.estimated_cost, 4)
