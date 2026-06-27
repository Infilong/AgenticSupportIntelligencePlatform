import json

from fastapi.testclient import TestClient


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


def test_audit_logs_record_admin_actions_and_metadata(client: TestClient) -> None:
    register(client, "audit-owner@example.com")
    token = login(client, "audit-owner@example.com")
    workspace = create_workspace(client, token)

    agent = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(token),
        json={"name": "Audit Agent", "token_budget": 4000},
    )
    assert agent.status_code == 201
    updated_agent = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent.json()['id']}",
        headers=auth_headers(token),
        json={"confidence_threshold": 0.8},
    )
    assert updated_agent.status_code == 200
    document = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Audit Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days. " * 40,
        },
    )
    assert document.status_code == 201
    model_config = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
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
    assert model_config.status_code == 201

    logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs", headers=auth_headers(token)
    )

    assert logs.status_code == 200
    body = logs.json()
    actions = [log["action"] for log in body]
    assert "agent.created" in actions
    assert "agent.updated" in actions
    assert "knowledge_document.uploaded" in actions
    assert "model_config.created" in actions
    model_log = next(log for log in body if log["action"] == "model_config.created")
    metadata = json.loads(model_log["metadata_json"])
    assert metadata["provider"] == "mock"
    assert metadata["model"] == "mock-cheap"
    assert all(log["workspace_id"] == workspace["id"] for log in body)
    assert all(log["actor_user_id"] is not None for log in body)


def test_audit_logs_are_workspace_scoped(client: TestClient) -> None:
    register(client, "audit-owner@example.com")
    owner_token = login(client, "audit-owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    agent = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/agents",
        headers=auth_headers(owner_token),
        json={"name": "Private Agent", "token_budget": 4000},
    )
    assert agent.status_code == 201

    register(client, "audit-other@example.com")
    other_token = login(client, "audit-other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    owner_logs = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/audit-logs",
        headers=auth_headers(owner_token),
    )
    other_logs = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/audit-logs",
        headers=auth_headers(other_token),
    )

    assert owner_logs.status_code == 200
    assert [log["action"] for log in owner_logs.json()] == ["agent.created"]
    assert other_logs.status_code == 200
    assert other_logs.json() == []
