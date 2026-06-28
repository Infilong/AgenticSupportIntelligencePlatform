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
    tools = response.json()
    assert [tool["name"] for tool in tools] == ["search_documents"]
    tool = tools[0]
    assert tool["framework"] == "langchain_core.tools.StructuredTool"
    assert tool["enabled"] is True
    assert tool["input_schema"]["properties"]["language"]["enum"] == ["en", "ja", "zh"]
    assert tool["usage"]["total_calls"] == 1
    assert tool["usage"]["failed_calls"] == 0
    assert tool["usage"]["last_used_at"] is not None
    assert tool["recent_calls"][0]["graph_run_id"] == run.json()["id"]
    assert tool["recent_calls"][0]["result_summary"] == "1 result(s) returned"


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
    other_tool = other_response.json()[0]
    assert other_tool["name"] == "search_documents"
    assert other_tool["usage"]["total_calls"] == 0
    assert other_tool["recent_calls"] == []
