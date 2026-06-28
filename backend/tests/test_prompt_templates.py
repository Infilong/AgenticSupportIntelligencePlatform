from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import PromptTemplate
from app.models.workspace import WorkspaceMember, WorkspaceRole


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




def add_member(db_session: Session, *, workspace_id: str, user_id: str) -> None:
    db_session.add(
        WorkspaceMember(
            workspace_id=UUID(workspace_id), user_id=UUID(user_id), role=WorkspaceRole.member
        )
    )
    db_session.commit()

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


def test_prompt_template_list_supports_search_status_and_offset(client: TestClient) -> None:
    register(client, "prompt-page-owner@example.com")
    token = login(client, "prompt-page-owner@example.com")
    workspace = create_workspace(client, token)
    path = f"/api/v1/workspaces/{workspace['id']}/prompt-templates"

    created: list[dict] = []
    for index in range(4):
        response = client.post(
            path,
            headers=auth_headers(token),
            json={
                "name": "support_response_drafter",
                "language": "en",
                "template_text": f"system: Prompt page {index}\nhuman: {{input_message}}",
                "active": index == 0,
            },
        )
        assert response.status_code == 201
        created.append(response.json())

    archived = client.delete(f"{path}/{created[1]['id']}", headers=auth_headers(token))
    first_page = client.get(path, headers=auth_headers(token), params={"limit": 2, "offset": 0})
    second_page = client.get(path, headers=auth_headers(token), params={"limit": 2, "offset": 2})
    active_page = client.get(path, headers=auth_headers(token), params={"status": "active"})
    draft_page = client.get(path, headers=auth_headers(token), params={"status": "draft"})
    archived_page = client.get(path, headers=auth_headers(token), params={"status": "archived"})
    search_page = client.get(path, headers=auth_headers(token), params={"search": "Prompt page 3"})

    assert archived.status_code == 204
    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert active_page.status_code == 200
    assert draft_page.status_code == 200
    assert archived_page.status_code == 200
    assert search_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1
    assert {item["id"] for item in first_page.json()}.isdisjoint(
        {item["id"] for item in second_page.json()}
    )
    assert [item["id"] for item in active_page.json()] == [created[0]["id"]]
    assert {item["id"] for item in draft_page.json()} == {created[2]["id"], created[3]["id"]}
    assert [item["id"] for item in archived_page.json()] == [created[1]["id"]]
    assert [item["id"] for item in search_page.json()] == [created[3]["id"]]


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


def test_prompt_template_archive_and_owner_only_mutation(
    client: TestClient, db_session: Session
) -> None:
    register(client, "prompt-lifecycle-owner@example.com")
    owner_token = login(client, "prompt-lifecycle-owner@example.com")
    workspace = create_workspace(client, owner_token)
    member = register(client, "prompt-lifecycle-member@example.com")
    member_token = login(client, "prompt-lifecycle-member@example.com")
    add_member(db_session, workspace_id=workspace["id"], user_id=member["id"])
    path = f"/api/v1/workspaces/{workspace['id']}/prompt-templates"

    member_create = client.post(
        path,
        headers=auth_headers(member_token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: member should not change prompts\nhuman: {input_message}",
            "active": True,
        },
    )
    assert member_create.status_code == 403
    assert member_create.json()["detail"]["code"] == "workspace_permission_required"
    assert member_create.json()["detail"]["required_permission"] == "prompts:write"

    created = client.post(
        path,
        headers=auth_headers(owner_token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: owner prompt lifecycle\nhuman: {input_message}",
            "active": True,
        },
    )
    assert created.status_code == 201

    member_archive = client.delete(
        f"{path}/{created.json()['id']}", headers=auth_headers(member_token)
    )
    assert member_archive.status_code == 403

    archived = client.delete(f"{path}/{created.json()['id']}", headers=auth_headers(owner_token))
    default_list = client.get(path, headers=auth_headers(owner_token))
    archived_list = client.get(f"{path}?include_archived=true", headers=auth_headers(owner_token))
    activate_archived = client.post(
        f"{path}/{created.json()['id']}/activate", headers=auth_headers(owner_token)
    )

    assert archived.status_code == 204
    assert default_list.status_code == 200
    assert default_list.json() == []
    assert archived_list.status_code == 200
    assert archived_list.json()[0]["archived_at"] is not None
    assert archived_list.json()[0]["active"] is False
    assert activate_archived.status_code == 404
    assert activate_archived.json()["detail"]["code"] == "prompt_template_not_found"

    recreated = client.post(
        path,
        headers=auth_headers(owner_token),
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: owner prompt lifecycle v2\nhuman: {input_message}",
            "active": True,
        },
    )
    assert recreated.status_code == 201
    assert recreated.json()["version"] == 2

    stored = db_session.scalars(select(PromptTemplate)).all()
    assert len(stored) == 2
    assert sum(1 for template in stored if template.archived_at is not None) == 1
