import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_evaluations import auth_headers, create_workspace, login, register

from app.core.config import get_settings
from app.models.ai import AIRun
from app.services.model_provider import UrllibOpenAIChatTransport


@pytest.mark.parametrize("fail", [False, True])
def test_direct_baseline_uses_configured_provider_and_records_outcome(
    client: TestClient, db_session: Session, monkeypatch, fail: bool,
):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    get_settings.cache_clear()
    calls = []

    def completion(self, **kwargs):
        calls.append(kwargs["prompt"])
        if fail:
            raise TimeoutError("synthetic provider timeout")
        return {"choices": [{"message": {"content": "A provider-generated baseline answer."}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 8, "total_tokens": 20}}

    monkeypatch.setattr(UrllibOpenAIChatTransport, "create_chat_completion", completion)
    register(client, "baseline-provider@example.com")
    token = login(client, "baseline-provider@example.com")
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}"
    config = client.post(base + "/model-configs", headers=auth_headers(token), json={
        "provider": "openai-compatible", "model": "test-baseline-model",
        "purpose": "evaluation_direct_llm", "prompt_token_cost_per_1k": 0.01,
        "completion_token_cost_per_1k": 0.02, "max_context_tokens": 8192, "active": True,
    })
    assert config.status_code == 201
    response = client.post(base + "/evaluations", headers=auth_headers(token), json={
        "name": "Configured baseline", "modes": ["direct_llm"],
        "jsonl_cases": json.dumps({"id": "baseline", "language": "en",
                                   "input_message": "What is the refund policy?",
                                   "expected_route": "finalize"}),
    })
    assert response.status_code == 201
    assert calls == ["What is the refund policy?"]
    result = response.json()["results"][0]
    ledger = db_session.scalar(select(AIRun).where(
        AIRun.workspace_id == UUID(workspace["id"]), AIRun.purpose == "evaluation_direct_llm",
    ))
    assert ledger is not None
    assert ledger.model == "test-baseline-model"
    if fail:
        assert result["actual_route"] == "error"
        assert result["error_message"]
        assert ledger.status == "failed"
    else:
        assert result["answer"] == "A provider-generated baseline answer."
        assert ledger.status == "succeeded"
        assert result["prompt_tokens"] == 12
        assert result["estimated_cost"] == ledger.estimated_cost > 0

    register(client, "baseline-outsider@example.com")
    outsider = login(client, "baseline-outsider@example.com")
    denied = client.post(base + "/evaluations", headers=auth_headers(outsider), json={
        "name": "Forbidden baseline", "modes": ["direct_llm"],
        "jsonl_cases": json.dumps({"id": "denied", "language": "en",
                                   "input_message": "Do not send this protected request.",
                                   "expected_route": "finalize"}),
    })
    assert denied.status_code == 404
    assert denied.json()["detail"]["code"] == "workspace_not_found"
    assert calls == ["What is the refund policy?"]
