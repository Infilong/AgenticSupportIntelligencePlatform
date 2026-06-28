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
    assert any(item["target_tab"] == "reviews" for item in body["items"])
    assert any(item["target_tab"] == "guardrails" for item in body["items"])


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
