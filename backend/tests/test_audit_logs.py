import json
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.audit_log_service import AuditLogService


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


def test_audit_logs_support_backend_search_actor_impact_and_offset(
    client: TestClient, db_session: Session
) -> None:
    register(client, "audit-filter-owner@example.com")
    token = login(client, "audit-filter-owner@example.com")
    workspace = create_workspace(client, token)

    agent = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(token),
        json={"name": "Audit Filter Agent", "token_budget": 4000},
    )
    assert agent.status_code == 201
    updated = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent.json()['id']}",
        headers=auth_headers(token),
        json={"confidence_threshold": 0.75},
    )
    assert updated.status_code == 200

    AuditLogService(db_session).record(
        workspace_id=UUID(workspace["id"]),
        actor_user_id=None,
        action="prompt_template.activated",
        resource_type="prompt_template",
        resource_id="activation-test",
        metadata={"note": "activation-test"},
    )
    AuditLogService(db_session).record(
        workspace_id=UUID(workspace["id"]),
        actor_user_id=None,
        action="system.heartbeat",
        resource_type="system",
        resource_id="system-low",
        metadata={"note": "system-low"},
    )

    first_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"limit": 2, "offset": 0},
    )
    second_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"limit": 2, "offset": 2},
    )
    user_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"actor": "user", "limit": 20},
    )
    system_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"actor": "system", "limit": 20},
    )
    high_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"impact": "high", "limit": 20},
    )
    medium_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"impact": "medium", "limit": 20},
    )
    low_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"impact": "low", "limit": 20},
    )
    search_logs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/audit-logs",
        headers=auth_headers(token),
        params={"search": "activation-test", "limit": 20},
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert user_logs.status_code == 200
    assert system_logs.status_code == 200
    assert high_logs.status_code == 200
    assert medium_logs.status_code == 200
    assert low_logs.status_code == 200
    assert search_logs.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 2
    assert {item["id"] for item in first_page.json()}.isdisjoint(
        {item["id"] for item in second_page.json()}
    )
    assert all(item["actor_user_id"] for item in user_logs.json())
    assert all(item["actor_user_id"] is None for item in system_logs.json())
    assert {item["action"] for item in high_logs.json()} == {"prompt_template.activated"}
    assert {item["action"] for item in medium_logs.json()} == {
        "agent.created",
        "agent.updated",
    }
    assert {item["action"] for item in low_logs.json()} == {"system.heartbeat"}
    assert [item["resource_id"] for item in search_logs.json()] == ["activation-test"]


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
