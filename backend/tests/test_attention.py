from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import (
    AgentConfig,
    GraphRun,
    GraphRunStatus,
    GraphStep,
    GraphStepStatus,
    ToolCall,
)
from app.models.ai import AIRun, AIRunStatus
from app.models.review import GuardrailResult
from app.models.user import User


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


def create_agent(client: TestClient, token: str, workspace_id: str) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/agents",
        headers=auth_headers(token),
        json={"name": "Attention Agent", "token_budget": 4000},
    )
    assert response.status_code == 201
    return response.json()


def test_attention_summary_reports_review_guardrail_and_cost_tasks(client: TestClient) -> None:
    register(client, "attention-owner@example.com")
    token = login(client, "attention-owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "How do I permanently delete my account?"},
    )
    assert run.status_code == 201
    assert run.json()["route_decision"] == "human_review"

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/attention",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    item_ids = {item["id"] for item in body["items"]}
    assert body["workspace_id"] == workspace["id"]
    assert body["pending_reviews"] == 1
    assert body["warning_count"] >= 1
    assert "pending_reviews" in item_ids
    assert "unassigned_reviews" in item_ids
    assert "guardrail_failures" in item_ids
    guardrail_item = next(item for item in body["items"] if item["id"] == "guardrail_failures")
    assert guardrail_item["target_tab"] == "trace"
    assert guardrail_item["target_id"] == run.json()["id"]
    assert any(item["target_tab"] == "reviews" for item in body["items"])


def test_attention_summary_counts_assigned_reviews(client: TestClient) -> None:
    user = register(client, "attention-reviewer@example.com")
    token = login(client, "attention-reviewer@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])
    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "How do I permanently delete my account?"},
    )
    assert run.status_code == 201
    reviews = client.get(
        f"/api/v1/workspaces/{workspace['id']}/human-reviews",
        headers=auth_headers(token),
    ).json()
    claim = client.post(
        f"/api/v1/workspaces/{workspace['id']}/human-reviews/{reviews[0]['id']}/claim",
        headers=auth_headers(token),
    )
    assert claim.status_code == 200
    assert claim.json()["reviewer_id"] == user["id"]

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/attention",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assigned_to_me_reviews"] == 1
    assert any(item["id"] == "assigned_reviews" for item in body["items"])


def test_attention_traceable_failures_include_graph_run_targets(
    client: TestClient, db_session: Session
) -> None:
    register(client, "attention-trace-target@example.com")
    token = login(client, "attention-trace-target@example.com")
    workspace = create_workspace(client, token)
    user = db_session.scalar(select(User).where(User.email == "attention-trace-target@example.com"))
    assert user is not None
    agent = AgentConfig(
        workspace_id=UUID(workspace["id"]),
        name="Trace Target Agent",
        token_budget=4000,
    )
    db_session.add(agent)
    db_session.flush()
    run = GraphRun(
        workspace_id=UUID(workspace["id"]),
        agent_config_id=agent.id,
        user_id=user.id,
        input_message="force traceable failure",
        language=SupportedLanguage.en,
        status=GraphRunStatus.failed,
        route_decision="failed",
    )
    db_session.add(run)
    db_session.flush()
    failed_step = GraphStep(
        workspace_id=UUID(workspace["id"]),
        graph_run_id=run.id,
        step_name="retrieve_evidence",
        input_json="{}",
        output_json="{}",
        status=GraphStepStatus.failed,
        latency_ms=8,
        error_message="tool failed",
        retry_count=0,
    )
    db_session.add(failed_step)
    db_session.flush()
    db_session.add(
        AIRun(
            workspace_id=UUID(workspace["id"]),
            graph_run_id=run.id,
            graph_step_id=failed_step.id,
            provider="mock",
            model="mock-failed",
            purpose="draft_response",
            language=SupportedLanguage.en,
            prompt_tokens=12,
            completion_tokens=0,
            total_tokens=12,
            estimated_cost=0.0,
            latency_ms=5,
            cache_hit=False,
            status=AIRunStatus.failed,
            error_message="provider failed",
        )
    )
    db_session.add(
        ToolCall(
            workspace_id=UUID(workspace["id"]),
            graph_run_id=run.id,
            graph_step_id=failed_step.id,
            tool_name="search_documents",
            input_json="{}",
            output_json="{}",
            status=GraphStepStatus.failed,
            latency_ms=8,
        )
    )
    db_session.add(
        GuardrailResult(
            workspace_id=UUID(workspace["id"]),
            graph_run_id=run.id,
            graph_step_id=failed_step.id,
            guardrail_type="citation_required",
            passed=False,
            severity="warning",
            message="citation missing",
        )
    )
    db_session.commit()

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/attention",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    items = {item["id"]: item for item in response.json()["items"]}
    assert items["failed_graph_runs"]["target_tab"] == "trace"
    assert items["failed_graph_runs"]["target_id"] == str(run.id)
    assert items["failed_model_calls"]["target_tab"] == "trace"
    assert items["failed_model_calls"]["target_id"] == str(run.id)
    assert items["tool_failures"]["target_tab"] == "trace"
    assert items["tool_failures"]["target_id"] == str(run.id)
    assert items["guardrail_failures"]["target_tab"] == "trace"
    assert items["guardrail_failures"]["target_id"] == str(run.id)


def test_attention_summary_is_workspace_scoped(client: TestClient) -> None:
    register(client, "attention-owner-a@example.com")
    token_a = login(client, "attention-owner-a@example.com")
    workspace_a = create_workspace(client, token_a, "Workspace A")
    register(client, "attention-owner-b@example.com")
    token_b = login(client, "attention-owner-b@example.com")
    create_workspace(client, token_b, "Workspace B")

    forbidden = client.get(
        f"/api/v1/workspaces/{workspace_a['id']}/attention",
        headers=auth_headers(token_b),
    )

    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "workspace_not_found"
