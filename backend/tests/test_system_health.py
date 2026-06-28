from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.ai import AIRun, AIRunStatus
from app.models.review import HumanReview, ReviewDecision
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


def create_workspace(client: TestClient, token: str, name: str = "Support Workspace") -> dict:
    response = client.post("/api/v1/workspaces", json={"name": name}, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def get_section(body: dict, section_id: str) -> dict:
    return next(section for section in body["sections"] if section["id"] == section_id)


def metric_value(section: dict, label: str):
    return next(metric["value"] for metric in section["metrics"] if metric["label"] == label)


def test_system_health_reports_workspace_readiness_and_provider_warning(client: TestClient) -> None:
    register(client, "health-owner@example.com")
    token = login(client, "health-owner@example.com")
    workspace = create_workspace(client, token)
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "purpose": "draft_response",
            "prompt_token_cost_per_1k": 0.0004,
            "completion_token_cost_per_1k": 0.0016,
            "max_context_tokens": 128000,
            "active": True,
        },
    )
    assert created.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/system-health",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    provider = get_section(body, "providers")
    assert body["workspace_id"] == workspace["id"]
    assert body["overall_status"] == "warning"
    assert provider["status"] == "warning"
    assert "OPENAI_API_KEY" in provider["summary"]
    assert metric_value(provider, "Live provider routes") == 1
    assert metric_value(provider, "OpenAI key") == "missing"


def test_system_health_is_workspace_scoped_for_members(
    client: TestClient, db_session: Session
) -> None:
    register(client, "health-owner-a@example.com")
    owner_token = login(client, "health-owner-a@example.com")
    workspace = create_workspace(client, owner_token, "Owner Workspace")
    member = register(client, "health-member@example.com")
    member_token = login(client, "health-member@example.com")
    db_session.add(
        WorkspaceMember(
            workspace_id=UUID(workspace["id"]),
            user_id=UUID(member["id"]),
            role=WorkspaceRole.member,
        )
    )
    db_session.commit()
    register(client, "health-other@example.com")
    other_token = login(client, "health-other@example.com")

    member_response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/system-health",
        headers=auth_headers(member_token),
    )
    forbidden = client.get(
        f"/api/v1/workspaces/{workspace['id']}/system-health",
        headers=auth_headers(other_token),
    )

    assert member_response.status_code == 200
    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "workspace_not_found"


def test_system_health_surfaces_operational_failures(
    client: TestClient, db_session: Session
) -> None:
    owner = register(client, "health-failures@example.com")
    token = login(client, "health-failures@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    user_id = UUID(owner["id"])
    agent = AgentConfig(workspace_id=workspace_id, name="Failure Agent", token_budget=2000)
    db_session.add(agent)
    db_session.flush()
    run = GraphRun(
        workspace_id=workspace_id,
        agent_config_id=agent.id,
        user_id=user_id,
        input_message="Failure case",
        language=SupportedLanguage.en,
        status=GraphRunStatus.failed,
        route_decision="failed",
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        HumanReview(
            workspace_id=workspace_id,
            graph_run_id=run.id,
            reason="confidence_threshold",
            proposed_answer="Needs operator review",
            reviewer_decision=ReviewDecision.pending,
        )
    )
    db_session.add(
        AIRun(
            workspace_id=workspace_id,
            graph_run_id=run.id,
            graph_step_id=None,
            provider="mock",
            model="mock-failure",
            purpose="draft_response",
            language=SupportedLanguage.en,
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            estimated_cost=0.0,
            latency_ms=3,
            cache_hit=False,
            status=AIRunStatus.failed,
            error_message="provider failed",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/system-health",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    operations = get_section(response.json(), "operations")
    assert operations["status"] == "critical"
    assert metric_value(operations, "Pending human reviews") == 1
    assert metric_value(operations, "Failed graph runs") == 1
    assert metric_value(operations, "Failed AI runs") == 1
