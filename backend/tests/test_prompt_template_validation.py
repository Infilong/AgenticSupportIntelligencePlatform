import hashlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services.support_prompts import build_classification_prompt


def _register_and_login(client: TestClient, email: str) -> str:
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "strong-password", "display_name": "Test User"},
    )
    assert register.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strong-password"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def _create_workspace(client: TestClient, token: str) -> dict:
    response = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Prompt Validation Workspace"},
    )
    assert response.status_code == 201
    return response.json()


def test_prompt_template_rejects_unsupported_runtime_variable(client: TestClient) -> None:
    token = _register_and_login(client, "prompt-invalid-variable@example.com")
    workspace = _create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/prompt-templates",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": "system: classify\nhuman: {input_message} {workspace_secret}",
            "active": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "prompt_template_invalid"
    assert "{workspace_secret}" in response.json()["detail"]["message"]


def test_prompt_template_rejects_missing_input_message(client: TestClient) -> None:
    token = _register_and_login(client, "prompt-missing-variable@example.com")
    workspace = _create_workspace(client, token)

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/prompt-templates",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "support_response_drafter",
            "language": "en",
            "template_text": "system: draft safely\nhuman: Language {language}",
            "active": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "prompt_template_invalid"
    assert "{input_message}" in response.json()["detail"]["message"]


def test_activated_prompt_controls_graph_provider_input(client: TestClient) -> None:
    token = _register_and_login(client, "prompt-runtime-integration@example.com")
    workspace = _create_workspace(client, token)
    headers = {"Authorization": f"Bearer {token}"}
    custom_text = (
        "system: ACTIVE CLASSIFIER INTEGRATION PROMPT\n"
        "human: Customer request: {input_message}"
    )
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/prompt-templates",
        headers=headers,
        json={
            "name": "support_intent_classifier",
            "language": "en",
            "template_text": custom_text,
            "active": True,
        },
    )
    document = client.post(
        f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=headers,
        json={
            "title": "Refund Policy",
            "content_type": "text/plain",
            "language": "en",
            "content": "Refunds are available within 30 days after purchase. " * 40,
        },
    )
    agent = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=headers,
        json={"name": "Prompt Runtime Agent", "token_budget": 4000},
    )
    run = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents/{agent.json()['id']}/runs",
        headers=headers,
        json={"input_message": "Can I get a refund within 30 days?"},
    )
    trace = client.get(
        f"/api/v1/workspaces/{workspace['id']}/agent-runs/{run.json()['id']}/trace",
        headers=headers,
    )

    assert created.status_code == 201
    assert document.status_code == 201
    assert agent.status_code == 201
    assert run.status_code == 201
    assert trace.status_code == 200
    classifier_run = next(
        item for item in trace.json()["ai_runs"] if item["purpose"] == "classification"
    )
    expected_prompt = build_classification_prompt(
        "Can I get a refund within 30 days?",
        prompt_template=SimpleNamespace(template_text=custom_text),
    )
    assert classifier_run["rendered_prompt_hash"] == hashlib.sha256(
        expected_prompt.encode("utf-8")
    ).hexdigest()
