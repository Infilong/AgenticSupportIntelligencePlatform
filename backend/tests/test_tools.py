import json
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphRun, GraphStep, GraphStepStatus, ToolCall
from app.models.user import User
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


def upload_document(client: TestClient, token: str, workspace_id: str) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": "Refund Policy EN",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days after purchase. " * 40,
        },
    )
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


def add_member(db_session: Session, *, workspace_id: str, user_email: str) -> None:
    user = db_session.query(User).filter_by(email=user_email).one()
    db_session.add(
        WorkspaceMember(workspace_id=UUID(workspace_id), user_id=user.id, role=WorkspaceRole.member)
    )
    db_session.commit()


def test_tools_catalog_exposes_runtime_tool_and_usage_from_graph_runs(client: TestClient) -> None:
    register(client, "tools-owner@example.com")
    token = login(client, "tools-owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "Can I get a refund within 30 days?"},
    )
    assert run.status_code == 201

    response = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    tools_body = response.json()
    assert tools_body["total"] == 1
    assert tools_body["has_next"] is False
    tools = tools_body["items"]
    assert [tool["name"] for tool in tools] == ["search_documents"]
    tool = tools[0]
    assert tool["framework"] == "langchain_core.tools.StructuredTool"
    assert tool["enabled"] is True
    assert tool["max_retries"] == 0
    assert tool["input_schema"]["properties"]["language"]["enum"] == ["en", "ja", "zh"]
    assert tool["usage"]["total_calls"] == 1
    assert tool["usage"]["failed_calls"] == 0
    assert tool["usage"]["last_used_at"] is not None
    recent_call = tool["recent_calls"][0]
    assert recent_call["graph_run_id"] == run.json()["id"]
    assert recent_call["step_name"] == "retrieve_evidence"
    assert recent_call["graph_run_status"] == "completed"
    assert recent_call["graph_run_input_message"] == "Can I get a refund within 30 days?"
    assert recent_call["graph_run_language"] == "en"
    assert recent_call["result_summary"] == "1 result(s) returned"
    assert json.loads(recent_call["input_json"])["query"] == "Can I get a refund within 30 days?"
    assert json.loads(recent_call["output_json"])["result_count"] == 1
    assert recent_call["error_message"] is None


def test_tools_catalog_is_workspace_scoped(client: TestClient) -> None:
    register(client, "tools-scope-owner@example.com")
    owner_token = login(client, "tools-scope-owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload_document(client, owner_token, owner_workspace["id"])
    agent = create_agent(client, owner_token, owner_workspace["id"])
    owner_run = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(owner_token),
        json={"input_message": "Can I get a refund within 30 days?"},
    )
    assert owner_run.status_code == 201

    register(client, "tools-scope-other@example.com")
    other_token = login(client, "tools-scope-other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    other_response = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/tools",
        headers=auth_headers(other_token),
    )

    assert other_response.status_code == 200
    other_body = other_response.json()
    assert other_body["total"] == 1
    other_tool = other_body["items"][0]
    assert other_tool["name"] == "search_documents"
    assert other_tool["usage"]["total_calls"] == 0
    assert other_tool["recent_calls"] == []


def test_owner_can_configure_tool_defaults(client: TestClient) -> None:
    register(client, "tools-config-owner@example.com")
    token = login(client, "tools-config-owner@example.com")
    workspace = create_workspace(client, token)

    updated = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tools/search_documents/config",
        headers=auth_headers(token),
        json={"enabled": False, "timeout_ms": 2500, "max_retries": 2},
    )
    listed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(token),
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["name"] == "search_documents"
    assert body["enabled"] is False
    assert body["timeout_ms"] == 2500
    assert body["max_retries"] == 2
    assert "2 automatic retries" in body["retry_policy"]
    assert listed.status_code == 200
    listed_body = listed.json()
    assert listed_body["total"] == 1
    assert listed_body["items"][0]["enabled"] is False
    assert listed_body["items"][0]["timeout_ms"] == 2500


def test_tool_configuration_requires_owner_and_is_workspace_scoped(
    client: TestClient, db_session: Session
) -> None:
    register(client, "tools-config-rbac-owner@example.com")
    owner_token = login(client, "tools-config-rbac-owner@example.com")
    workspace = create_workspace(client, owner_token)
    register(client, "tools-config-rbac-member@example.com")
    member_token = login(client, "tools-config-rbac-member@example.com")
    add_member(
        db_session,
        workspace_id=workspace["id"],
        user_email="tools-config-rbac-member@example.com",
    )
    register(client, "tools-config-rbac-other@example.com")
    other_token = login(client, "tools-config-rbac-other@example.com")

    member_update = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tools/search_documents/config",
        headers=auth_headers(member_token),
        json={"enabled": False},
    )
    other_update = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tools/search_documents/config",
        headers=auth_headers(other_token),
        json={"enabled": False},
    )
    unknown_tool = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tools/not_real/config",
        headers=auth_headers(owner_token),
        json={"enabled": False},
    )

    assert member_update.status_code == 403
    assert member_update.json()["detail"]["code"] == "workspace_permission_required"
    assert member_update.json()["detail"]["required_permission"] == "tools:configure"
    assert other_update.status_code == 404
    assert other_update.json()["detail"]["code"] == "workspace_not_found"
    assert unknown_tool.status_code == 404
    assert unknown_tool.json()["detail"]["code"] == "tool_not_found"


def test_disabled_retrieval_tool_routes_agent_to_review_and_records_failed_tool_call(
    client: TestClient,
) -> None:
    register(client, "tools-disabled-owner@example.com")
    token = login(client, "tools-disabled-owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])
    config = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/tools/search_documents/config",
        headers=auth_headers(token),
        json={"enabled": False, "max_retries": 1},
    )
    assert config.status_code == 200

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "Can I get a refund within 30 days?"},
    )
    tools = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(token),
    )
    trace = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agent-runs/{run.json()['id']}/trace",
        headers=auth_headers(token),
    )

    assert run.status_code == 201
    assert run.json()["route_decision"] == "human_review"
    assert tools.status_code == 200
    tools_body = tools.json()
    assert tools_body["total"] == 1
    tool = tools_body["items"][0]
    assert tool["enabled"] is False
    assert tool["usage"]["failed_calls"] == 1
    failed_call = tool["recent_calls"][0]
    assert failed_call["result_summary"] == "Tool disabled by workspace config"
    assert failed_call["step_name"] == "retrieve_evidence"
    assert failed_call["graph_run_status"] == "needs_human_review"
    assert (
        failed_call["error_message"] == "search_documents disabled by workspace tool configuration"
    )
    assert json.loads(failed_call["output_json"])["tool_disabled"] is True
    retrieve_step = next(
        step for step in trace.json()["steps"] if step["step_name"] == "retrieve_evidence"
    )
    assert retrieve_step["status"] == "failed"
    assert retrieve_step["tool_calls"][0]["status"] == "failed"
    assert "disabled" in retrieve_step["error_message"]


def test_tools_catalog_supports_backend_search_view_and_pagination(
    client: TestClient, db_session: Session
) -> None:
    owner = register(client, "tools-filter-owner@example.com")
    token = login(client, "tools-filter-owner@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    agent = AgentConfig(workspace_id=workspace_id, name="Tool Filter Agent")
    db_session.add(agent)
    db_session.flush()
    run = GraphRun(
        workspace_id=workspace_id,
        agent_config_id=agent.id,
        user_id=UUID(owner["id"]),
        input_message="custom tool failed during retrieval",
        language=SupportedLanguage.en,
        status="failed",
    )
    db_session.add(run)
    db_session.flush()
    step = GraphStep(
        workspace_id=workspace_id,
        graph_run_id=run.id,
        step_name="custom_node",
        input_json="{}",
        output_json="{}",
        status=GraphStepStatus.failed,
        latency_ms=42,
        error_message="custom tool timeout",
    )
    db_session.add(step)
    db_session.flush()
    db_session.add(
        ToolCall(
            workspace_id=workspace_id,
            graph_run_id=run.id,
            graph_step_id=step.id,
            tool_name="custom_search_tool",
            input_json='{"query": "custom"}',
            output_json='{"error": "timeout"}',
            status=GraphStepStatus.failed,
            latency_ms=42,
        )
    )
    db_session.commit()

    failed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(token),
        params={"view": "failed", "search": "custom", "limit": 1},
    )
    next_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/tools",
        headers=auth_headers(token),
        params={"view": "failed", "search": "custom", "limit": 1, "offset": 1},
    )

    assert failed.status_code == 200
    failed_body = failed.json()
    assert failed_body["total"] == 1
    assert failed_body["limit"] == 1
    assert failed_body["offset"] == 0
    assert failed_body["has_next"] is False
    assert [tool["name"] for tool in failed_body["items"]] == ["custom_search_tool"]
    assert failed_body["items"][0]["usage"]["failed_calls"] == 1
    assert failed_body["items"][0]["recent_calls"][0]["error_message"] == "custom tool timeout"
    assert next_page.status_code == 200
    next_body = next_page.json()
    assert next_body["total"] == 1
    assert next_body["offset"] == 1
    assert next_body["has_next"] is False
    assert next_body["items"] == []
