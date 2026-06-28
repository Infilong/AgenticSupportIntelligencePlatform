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


def guardrail_by_type(items: list[dict], guardrail_type: str) -> dict:
    return next(item for item in items if item["guardrail_type"] == guardrail_type)


def test_guardrail_catalog_exposes_runtime_policies_and_failures(client: TestClient) -> None:
    register(client, "guardrails-owner@example.com")
    token = login(client, "guardrails-owner@example.com")
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
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    guardrails = response.json()
    guardrail_types = {item["guardrail_type"] for item in guardrails}
    assert guardrail_types >= {
        "prompt_injection",
        "citation_required",
        "unsupported_answer",
        "confidence_threshold",
        "language_preservation",
    }
    citation = guardrail_by_type(guardrails, "citation_required")
    unsupported = guardrail_by_type(guardrails, "unsupported_answer")
    assert citation["enabled"] is True
    assert citation["action_on_fail"] == "route_to_human_review"
    assert citation["usage"]["failed_evaluations"] == 1
    assert citation["recent_failures"][0]["graph_run_id"] == run.json()["id"]
    assert unsupported["usage"]["failed_evaluations"] == 1
    assert unsupported["recent_failures"][0]["severity"] == "high"


def test_guardrail_catalog_is_workspace_scoped(client: TestClient) -> None:
    register(client, "guardrails-scope-owner@example.com")
    owner_token = login(client, "guardrails-scope-owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload_document(client, owner_token, owner_workspace["id"])
    agent = create_agent(client, owner_token, owner_workspace["id"])
    owner_run = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(owner_token),
        json={"input_message": "How do I permanently delete my account?"},
    )
    assert owner_run.status_code == 201

    register(client, "guardrails-scope-other@example.com")
    other_token = login(client, "guardrails-scope-other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    other_response = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/guardrails",
        headers=auth_headers(other_token),
    )

    assert other_response.status_code == 200
    citation = guardrail_by_type(other_response.json(), "citation_required")
    assert citation["usage"]["total_evaluations"] == 0
    assert citation["recent_failures"] == []
