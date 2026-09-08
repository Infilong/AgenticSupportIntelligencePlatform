import json

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
    guardrails_body = response.json()
    assert guardrails_body["total"] >= 5
    assert guardrails_body["has_next"] is False
    guardrails = guardrails_body["items"]
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
    assert citation["recent_failures"][0]["graph_step_id"] is not None
    assert unsupported["usage"]["failed_evaluations"] == 1
    assert unsupported["recent_failures"][0]["severity"] == "high"


def test_privacy_safety_and_escalation_guardrails_are_recorded_in_trace_and_catalog(
    client: TestClient,
) -> None:
    register(client, "guardrails-privacy-owner@example.com")
    token = login(client, "guardrails-privacy-owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "我要投诉，你们泄露了我的个人信息。"},
    )
    assert run.status_code == 201
    assert run.json()["route_decision"] == "human_review"

    trace = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agent-runs/{run.json()['id']}/trace",
        headers=auth_headers(token),
    )
    catalog = client.get(
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
    )

    assert trace.status_code == 200
    trace_guardrails = {item["guardrail_type"]: item for item in trace.json()["guardrails"]}
    for guardrail_type in ["privacy_complaint", "high_safety_risk", "escalation_needed"]:
        assert guardrail_type in trace_guardrails
        assert trace_guardrails[guardrail_type]["passed"] is False
        assert trace_guardrails[guardrail_type]["graph_step_id"] is not None

    assert catalog.status_code == 200
    catalog_guardrails = catalog.json()["items"]
    privacy = guardrail_by_type(catalog_guardrails, "privacy_complaint")
    safety = guardrail_by_type(catalog_guardrails, "high_safety_risk")
    escalation = guardrail_by_type(catalog_guardrails, "escalation_needed")
    assert privacy["usage"]["failed_evaluations"] == 1
    assert safety["usage"]["failed_evaluations"] == 1
    assert escalation["usage"]["failed_evaluations"] == 1
    assert privacy["recent_failures"][0]["graph_run_id"] == run.json()["id"]
    assert safety["recent_failures"][0]["severity"] == "high"
    assert escalation["recent_failures"][0]["severity"] == "medium"


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
    other_body = other_response.json()
    assert other_body["total"] >= 5
    citation = guardrail_by_type(other_body["items"], "citation_required")
    assert citation["usage"]["total_evaluations"] == 0
    assert citation["recent_failures"] == []


def test_owner_can_update_guardrail_policy_and_catalog_shows_effective_values(
    client: TestClient,
) -> None:
    register(client, "guardrail-policy-owner@example.com")
    token = login(client, "guardrail-policy-owner@example.com")
    workspace = create_workspace(client, token)

    response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/guardrails/citation_required/policy",
        headers=auth_headers(token),
        json={
            "enabled": False,
            "severity": "low",
            "action_on_fail": "record_only",
            "threshold": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["guardrail_type"] == "citation_required"
    assert body["enabled"] is False
    assert body["severity"] == "low"
    assert body["action_on_fail"] == "record_only"

    catalog = client.get(
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
    )
    assert catalog.status_code == 200
    catalog_body = catalog.json()
    assert catalog_body["total"] >= 5
    citation = guardrail_by_type(catalog_body["items"], "citation_required")
    assert citation["enabled"] is False
    assert citation["action_on_fail"] == "record_only"


def test_guardrail_policy_updates_require_owner_and_configurable_policy(
    client: TestClient,
) -> None:
    register(client, "guardrail-policy-owner-2@example.com")
    owner_token = login(client, "guardrail-policy-owner-2@example.com")
    workspace = create_workspace(client, owner_token)
    register(client, "guardrail-policy-member@example.com")
    member_token = login(client, "guardrail-policy-member@example.com")
    add_member = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=auth_headers(owner_token),
        json={"email": "guardrail-policy-member@example.com", "role": "operator"},
    )
    assert add_member.status_code == 201

    member_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/guardrails/citation_required/policy",
        headers=auth_headers(member_token),
        json={"enabled": False, "severity": "low", "action_on_fail": "record_only"},
    )
    fixed_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/guardrails/prompt_injection/policy",
        headers=auth_headers(owner_token),
        json={"enabled": False, "severity": "low", "action_on_fail": "record_only"},
    )
    missing_response = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/guardrails/not_real/policy",
        headers=auth_headers(owner_token),
        json={"enabled": False, "severity": "low", "action_on_fail": "record_only"},
    )

    assert member_response.status_code == 403
    assert member_response.json()["detail"]["code"] == "workspace_permission_required"
    assert member_response.json()["detail"]["required_permission"] == "guardrails:configure"
    assert fixed_response.status_code == 400
    assert fixed_response.json()["detail"]["code"] == "guardrail_policy_not_configurable"
    assert missing_response.status_code == 404
    assert missing_response.json()["detail"]["code"] == "guardrail_policy_not_found"


def test_disabled_citation_guardrail_is_removed_from_route_trace(
    client: TestClient,
) -> None:
    register(client, "guardrail-policy-runtime@example.com")
    token = login(client, "guardrail-policy-runtime@example.com")
    workspace = create_workspace(client, token)
    agent = create_agent(client, token, workspace["id"])
    policy = client.patch(
        f"/api/v1/workspaces/{workspace['id']}/guardrails/citation_required/policy",
        headers=auth_headers(token),
        json={
            "enabled": False,
            "severity": "medium",
            "action_on_fail": "route_to_human_review",
            "threshold": None,
        },
    )
    assert policy.status_code == 200

    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "How do I permanently delete my account?"},
    )
    assert run.status_code == 201
    assert run.json()["route_decision"] == "human_review"

    trace = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agent-runs/{run.json()['id']}/trace",
        headers=auth_headers(token),
    )
    assert trace.status_code == 200
    route_step = next(
        step for step in trace.json()["steps"] if step["step_name"] == "route_review_or_finalize"
    )
    route_output = json.loads(route_step["output_json"])
    assert "citation_required" not in route_output["route_reasons"]
    guardrails = trace.json()["guardrails"]
    guardrail_types = {item["guardrail_type"] for item in guardrails}
    assert "citation_required" not in guardrail_types
    assert "unsupported_answer" in guardrail_types
    assert all(item["graph_step_id"] == route_step["id"] for item in guardrails)


def test_guardrail_catalog_supports_backend_search_view_and_pagination(
    client: TestClient,
) -> None:
    register(client, "guardrails-filter-owner@example.com")
    token = login(client, "guardrails-filter-owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"])
    agent = create_agent(client, token, workspace["id"])
    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent['id']}/runs",
        headers=auth_headers(token),
        json={"input_message": "How do I permanently delete my account?"},
    )
    assert run.status_code == 201

    failed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
        params={"view": "failed", "search": "unsupported", "limit": 1},
    )
    next_page = client.get(
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
        params={"view": "failed", "search": "unsupported", "limit": 1, "offset": 1},
    )
    fixed = client.get(
        f"/api/v1/workspaces/{workspace['id']}/guardrails",
        headers=auth_headers(token),
        params={"view": "fixed", "search": "prompt injection"},
    )

    assert failed.status_code == 200
    failed_body = failed.json()
    assert failed_body["total"] == 1
    assert failed_body["limit"] == 1
    assert failed_body["offset"] == 0
    assert failed_body["has_next"] is False
    assert [item["guardrail_type"] for item in failed_body["items"]] == ["unsupported_answer"]
    assert failed_body["items"][0]["recent_failures"]
    assert next_page.status_code == 200
    next_body = next_page.json()
    assert next_body["total"] == 1
    assert next_body["offset"] == 1
    assert next_body["has_next"] is False
    assert next_body["items"] == []
    assert fixed.status_code == 200
    fixed_body = fixed.json()
    assert fixed_body["total"] == 1
    assert [item["guardrail_type"] for item in fixed_body["items"]] == ["prompt_injection"]
