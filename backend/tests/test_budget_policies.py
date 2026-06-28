from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.ai import AIRun, AIRunStatus
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


def create_workspace(client: TestClient, token: str, name: str = "Budget Workspace") -> dict:
    response = client.post("/api/v1/workspaces", json={"name": name}, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def add_member(db_session: Session, *, workspace_id: str, user_id: str) -> None:
    db_session.add(
        WorkspaceMember(
            workspace_id=UUID(workspace_id), user_id=UUID(user_id), role=WorkspaceRole.member
        )
    )
    db_session.commit()


def test_budget_policy_defaults_update_permissions_and_workspace_scope(
    client: TestClient, db_session: Session
) -> None:
    register(client, "budget-owner@example.com")
    owner_token = login(client, "budget-owner@example.com")
    workspace = create_workspace(client, owner_token)

    defaults = client.get(
        f"/api/v1/workspaces/{workspace['id']}/budget-policy",
        headers=auth_headers(owner_token),
    )
    assert defaults.status_code == 200
    assert defaults.json()["monthly_token_budget"] == 100000
    assert defaults.json()["rate_limit_requests_per_hour"] == 60

    updated = client.put(
        f"/api/v1/workspaces/{workspace['id']}/budget-policy",
        headers=auth_headers(owner_token),
        json={
            "monthly_token_budget": 2000,
            "monthly_cost_budget": 1.5,
            "per_run_token_budget": 1200,
            "per_run_cost_budget": 0.02,
            "rate_limit_requests_per_hour": 7,
            "alert_threshold_percent": 0.75,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["per_run_token_budget"] == 1200
    assert updated.json()["alert_threshold_percent"] == 0.75

    member = register(client, "budget-member@example.com")
    member_token = login(client, "budget-member@example.com")
    add_member(db_session, workspace_id=workspace["id"], user_id=member["id"])
    member_update = client.put(
        f"/api/v1/workspaces/{workspace['id']}/budget-policy",
        headers=auth_headers(member_token),
        json={
            "monthly_token_budget": 3000,
            "monthly_cost_budget": 2.0,
            "per_run_token_budget": 1200,
            "per_run_cost_budget": 0.02,
            "rate_limit_requests_per_hour": 7,
            "alert_threshold_percent": 0.75,
        },
    )
    assert member_update.status_code == 403
    assert member_update.json()["detail"]["code"] == "workspace_owner_required"

    register(client, "budget-other@example.com")
    other_token = login(client, "budget-other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Budget Workspace")
    cross_workspace = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/budget-policy",
        headers=auth_headers(owner_token),
    )
    assert cross_workspace.status_code == 404
    assert cross_workspace.json()["detail"]["code"] == "workspace_not_found"


def test_cost_summary_and_system_health_report_budget_policy(
    client: TestClient, db_session: Session
) -> None:
    owner = register(client, "budget-cost-owner@example.com")
    token = login(client, "budget-cost-owner@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    user_id = UUID(owner["id"])
    updated = client.put(
        f"/api/v1/workspaces/{workspace['id']}/budget-policy",
        headers=auth_headers(token),
        json={
            "monthly_token_budget": 1000,
            "monthly_cost_budget": 0.10,
            "per_run_token_budget": 900,
            "per_run_cost_budget": 0.01,
            "rate_limit_requests_per_hour": 10,
            "alert_threshold_percent": 0.5,
        },
    )
    assert updated.status_code == 200
    agent = AgentConfig(workspace_id=workspace_id, name="Budget Agent", token_budget=4000)
    db_session.add(agent)
    db_session.flush()
    run = GraphRun(
        workspace_id=workspace_id,
        agent_config_id=agent.id,
        user_id=user_id,
        input_message="Budget run",
        language=SupportedLanguage.en,
        status=GraphRunStatus.completed,
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(
        AIRun(
            workspace_id=workspace_id,
            graph_run_id=run.id,
            graph_step_id=None,
            provider="mock",
            model="mock-standard",
            purpose="draft_response",
            language=SupportedLanguage.en,
            prompt_tokens=300,
            completion_tokens=300,
            total_tokens=600,
            estimated_cost=0.06,
            latency_ms=20,
            cache_hit=False,
            status=AIRunStatus.succeeded,
        )
    )
    db_session.commit()

    costs = client.get(
        f"/api/v1/workspaces/{workspace['id']}/costs/summary",
        headers=auth_headers(token),
    )
    health = client.get(
        f"/api/v1/workspaces/{workspace['id']}/system-health",
        headers=auth_headers(token),
    )

    assert costs.status_code == 200
    budget = costs.json()["budget_policy"]
    assert budget["monthly_token_budget"] == 1000
    assert budget["tokens_used_this_month"] == 600
    assert budget["token_budget_used_percent"] == 0.6
    assert budget["alerting"] is True
    assert health.status_code == 200
    budget_section = next(
        section for section in health.json()["sections"] if section["id"] == "budgets"
    )
    assert budget_section["status"] == "warning"
    assert any(
        metric["label"] == "Rate limits" and metric["value"] == "10/hour"
        for metric in budget_section["metrics"]
    )


def test_workspace_rate_limit_blocks_agent_run(client: TestClient, db_session: Session) -> None:
    owner = register(client, "budget-rate-owner@example.com")
    token = login(client, "budget-rate-owner@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    user_id = UUID(owner["id"])
    agent_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(token),
        json={"name": "Rate Limited Agent", "token_budget": 4000},
    )
    assert agent_response.status_code == 201
    agent_id = UUID(agent_response.json()["id"])
    policy = client.put(
        f"/api/v1/workspaces/{workspace['id']}/budget-policy",
        headers=auth_headers(token),
        json={
            "monthly_token_budget": 100000,
            "monthly_cost_budget": 10.0,
            "per_run_token_budget": 1500,
            "per_run_cost_budget": 0.05,
            "rate_limit_requests_per_hour": 1,
            "alert_threshold_percent": 0.8,
        },
    )
    assert policy.status_code == 200
    db_session.add(
        GraphRun(
            workspace_id=workspace_id,
            agent_config_id=agent_id,
            user_id=user_id,
            input_message="Existing request",
            language=SupportedLanguage.en,
            status=GraphRunStatus.completed,
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent_response.json()['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "Can I get a refund?"},
    )

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "agent_rate_limit_exceeded"
