from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, ModelConfig
from app.services.model_provider import MockModelProvider, MockModelProviderError
from app.services.token_accounting import estimate_cost, estimate_tokens


def register(client: TestClient, email: str, password: str = "strong-password") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Test User"},
    )
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str, password: str = "strong-password") -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_workspace(client: TestClient, token: str, name: str = "Support Workspace") -> dict:
    response = client.post("/api/v1/workspaces", json={"name": name}, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def test_model_config_admin_can_create_list_and_activate_configs(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-admin@example.com")
    token = login(client, "model-admin@example.com")
    workspace = create_workspace(client, token)
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"

    first = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock",
            "model": "mock-cheap",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.0001,
            "completion_token_cost_per_1k": 0.0002,
            "max_context_tokens": 4096,
            "active": True,
        },
    )
    second = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock-admin",
            "model": "mock-admin-classifier",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.002,
            "completion_token_cost_per_1k": 0.003,
            "max_context_tokens": 16384,
            "active": False,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["active"] is True
    assert second.json()["active"] is False

    activated = client.post(f"{path}/{second.json()['id']}/activate", headers=auth_headers(token))
    listed = client.get(path, headers=auth_headers(token))

    assert activated.status_code == 200
    assert activated.json()["active"] is True
    assert listed.status_code == 200
    active_models = [item["model"] for item in listed.json() if item["active"]]
    assert active_models == ["mock-admin-classifier"]
    stored = db_session.scalars(select(ModelConfig)).all()
    assert {config.model for config in stored} == {"mock-cheap", "mock-admin-classifier"}


def test_model_configs_are_workspace_scoped(client: TestClient) -> None:
    register(client, "owner-model@example.com")
    owner_token = login(client, "owner-model@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner")
    register(client, "other-model@example.com")
    other_token = login(client, "other-model@example.com")
    other_workspace = create_workspace(client, other_token, "Other")

    created = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/model-configs",
        headers=auth_headers(owner_token),
        json={
            "provider": "mock-owner",
            "model": "mock-owner-model",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.001,
            "completion_token_cost_per_1k": 0.002,
            "max_context_tokens": 8192,
            "active": True,
        },
    )
    forbidden_activate = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/model-configs/{created.json()['id']}/activate",
        headers=auth_headers(other_token),
    )
    other_list = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/model-configs",
        headers=auth_headers(other_token),
    )

    assert created.status_code == 201
    assert forbidden_activate.status_code == 404
    assert forbidden_activate.json()["detail"]["code"] == "model_config_not_found"
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_active_model_config_controls_provider_pricing_and_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-run@example.com")
    token = login(client, "model-run@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"
    created = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock-admin",
            "model": "mock-admin-classifier",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.01,
            "completion_token_cost_per_1k": 0.02,
            "max_context_tokens": 32768,
            "active": True,
        },
    )
    assert created.status_code == 201

    prompt = "Classify this refund request."
    completion = "refund_request"
    response = MockModelProvider(db_session).complete(
        workspace_id=workspace_id,
        purpose="classification",
        language=SupportedLanguage.en,
        prompt=prompt,
        model="mock-cheap",
        completion_text=completion,
    )

    prompt_tokens = estimate_tokens(prompt, SupportedLanguage.en)
    completion_tokens = estimate_tokens(completion, SupportedLanguage.en)
    expected_cost = estimate_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_token_cost_per_1k=0.01,
        completion_token_cost_per_1k=0.02,
    )
    stored = db_session.scalar(select(AIRun).where(AIRun.id == response.ai_run.id))
    assert stored is not None
    assert stored.provider == "mock-admin"
    assert stored.model == "mock-admin-classifier"
    assert stored.estimated_cost == expected_cost


def test_active_model_config_context_limit_records_failed_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-limit@example.com")
    token = login(client, "model-limit@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "mock-limit",
            "model": "mock-tiny-context",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.01,
            "completion_token_cost_per_1k": 0.02,
            "max_context_tokens": 256,
            "active": True,
        },
    )
    assert created.status_code == 201

    try:
        MockModelProvider(db_session).complete(
            workspace_id=workspace_id,
            purpose="classification",
            language=SupportedLanguage.en,
            prompt="token " * 300,
            model="mock-cheap",
            completion_text="refund_request",
        )
    except MockModelProviderError as exc:
        assert "model_context_exceeded" in str(exc)
    else:
        raise AssertionError("expected model context error")

    stored = db_session.scalar(select(AIRun).where(AIRun.workspace_id == workspace_id))
    assert stored is not None
    assert stored.provider == "mock-limit"
    assert stored.model == "mock-tiny-context"
    assert stored.status == "failed"
    assert stored.error_message is not None
    assert "model_context_exceeded" in stored.error_message
    assert stored.estimated_cost == 0
