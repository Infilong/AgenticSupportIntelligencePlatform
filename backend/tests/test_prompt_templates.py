from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import PromptTemplate


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


def create_agent(client: TestClient, token: str, workspace_id: str) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/agents",
        headers=auth_headers(token),
        json={"name": "Support Agent", "token_budget": 4000},
    )
    assert response.status_code == 201
    return response.json()


def upload_document(client: TestClient, token: str, workspace_id: str) -> None:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days after purchase. " * 40,
        },
    )
    assert response.status_code == 201


def test_prompt_template_admin_can_create_list_and_activate_versions(
    client: TestClient, db_session: Session
) -> None:
    register(client, "prompt-admin@example.com")
    token = login(client, "prompt-admin@example.com")
    workspace = create_workspace(client, token)
    path = f"/api/v1/workspaces/{workspace['id']}/prompt-templates"

    created = client.post(
        path,
        headers=auth_headers(token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: classify safely\nhuman: {input_message}",
            "active": True,
        },
    )
    second = client.post(
        path,
        headers=auth_headers(token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: classify safely v2\nhuman: {input_message}",
            "active": False,
        },
    )
    assert created.status_code == 201
    assert second.status_code == 201
    assert created.json()["version"] == 1
    assert second.json()["version"] == 2
    assert second.json()["active"] is False

    activated = client.post(
        f"{path}/{second.json()['id']}/activate", headers=auth_headers(token)
    )
    listed = client.get(path, headers=auth_headers(token))

    assert activated.status_code == 200
    assert activated.json()["active"] is True
    assert listed.status_code == 200
    active_versions = [item["version"] for item in listed.json() if item["active"]]
    assert active_versions == [2]
    stored = db_session.scalars(select(PromptTemplate)).all()
    assert {template.version for template in stored} == {1, 2}


def test_active_prompt_template_is_used_by_next_agent_run(client: TestClient) -> None:
    register(client, "prompt-run@example.com")
    token = login(client, "prompt-run@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])
    path = f"/api/v1/workspaces/{workspace['id']}/prompt-templates"

    custom = client.post(
        path,
        headers=auth_headers(token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": (
                "system: custom classifier prompt for admin test\n"
                "human: {input_message}"
            ),
            "active": True,
        },
    )
    assert custom.status_code == 201

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "Can I get a refund within 30 days?"},
    )
    trace = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agent-runs/{run.json()['id']}/trace",
        headers=auth_headers(token),
    )

    assert run.status_code == 201
    classifier_run = next(
        item for item in trace.json()["ai_runs"] if item["purpose"] == "classification"
    )
    assert classifier_run["prompt_template_name"] == "support_intent_classifier"
    assert classifier_run["prompt_version"] == 1
    assert "custom classifier prompt" in classifier_run["prompt_template_text"]


def test_prompt_templates_are_workspace_scoped(client: TestClient) -> None:
    register(client, "owner-prompt@example.com")
    owner_token = login(client, "owner-prompt@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner")
    register(client, "other-prompt@example.com")
    other_token = login(client, "other-prompt@example.com")
    other_workspace = create_workspace(client, other_token, "Other")

    created = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/prompt-templates",
        headers=auth_headers(owner_token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: owner only prompt\nhuman: {input_message}",
            "active": True,
        },
    )
    forbidden_activate = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/prompt-templates/{created.json()['id']}/activate",
        headers=auth_headers(other_token),
    )
    other_list = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/prompt-templates",
        headers=auth_headers(other_token),
    )

    assert created.status_code == 201
    assert forbidden_activate.status_code == 404
    assert forbidden_activate.json()["detail"]["code"] == "prompt_template_not_found"
    assert other_list.status_code == 200
    assert other_list.json() == []
