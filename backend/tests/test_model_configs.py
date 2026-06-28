from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig
from app.models.ai import AIRun, ModelConfig
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.model_provider import (
    ConfiguredModelProvider,
    MockModelProvider,
    MockModelProviderError,
    ModelProviderError,
    OpenAICompatibleModelProvider,
)
from app.services.token_accounting import estimate_cost, estimate_tokens


class FakeOpenAITransport:
    def __init__(self, content: str = "Grounded OpenAI answer"):
        self.content = content
        self.calls: list[dict] = []

    def create_chat_completion(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        timeout_seconds: int,
    ) -> dict:
        self.calls.append(
            {
                "api_key": api_key,
                "base_url": base_url,
                "model": model,
                "prompt": prompt,
                "timeout_seconds": timeout_seconds,
            }
        )
        return {
            "choices": [{"message": {"content": self.content}}],
            "usage": {"prompt_tokens": 42, "completion_tokens": 11, "total_tokens": 53},
        }


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


def test_model_config_admin_can_create_list_and_activate_configs(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-admin@example.com")
    token = login(client, "model-admin@example.com")
    workspace = create_workspace(client, token)
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"

    first = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock",
            "model": "mock-cheap",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.0001,
            "completion_token_cost_per_1k": 0.0002,
            "max_context_tokens": 4096,
            "active": True,
        },
    )
    second = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock-admin",
            "model": "mock-admin-classifier",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.002,
            "completion_token_cost_per_1k": 0.003,
            "max_context_tokens": 16384,
            "active": False,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["active"] is True
    assert second.json()["active"] is False

    activated = client.post(f"{path}/{second.json()['id']}/activate", headers=auth_headers(token))
    listed = client.get(path, headers=auth_headers(token))

    assert activated.status_code == 200
    assert activated.json()["active"] is True
    assert listed.status_code == 200
    active_models = [item["model"] for item in listed.json() if item["active"]]
    assert active_models == ["mock-admin-classifier"]
    stored = db_session.scalars(select(ModelConfig)).all()
    assert {config.model for config in stored} == {"mock-cheap", "mock-admin-classifier"}


def test_model_config_list_supports_search_status_and_offset(client: TestClient) -> None:
    register(client, "model-page-owner@example.com")
    token = login(client, "model-page-owner@example.com")
    workspace = create_workspace(client, token)
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"

    created: list[dict] = []
    for index in range(4):
        response = client.post(
            path,
            headers=auth_headers(token),
            json={
                "provider": "mock-page",
                "model": f"mock-page-model-{index}",
                "purpose": "classification",
                "prompt_token_cost_per_1k": 0.001 + index,
                "completion_token_cost_per_1k": 0.002 + index,
                "max_context_tokens": 4096 + index,
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
    search_page = client.get(
        path, headers=auth_headers(token), params={"search": "mock-page-model-3"}
    )

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


def test_model_configs_are_workspace_scoped(client: TestClient) -> None:
    register(client, "owner-model@example.com")
    owner_token = login(client, "owner-model@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner")
    register(client, "other-model@example.com")
    other_token = login(client, "other-model@example.com")
    other_workspace = create_workspace(client, other_token, "Other")

    created = client.post(
        f"/api/v1/workspaces/{owner_workspace['id']}/model-configs",
        headers=auth_headers(owner_token),
        json={
            "provider": "mock-owner",
            "model": "mock-owner-model",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.001,
            "completion_token_cost_per_1k": 0.002,
            "max_context_tokens": 8192,
            "active": True,
        },
    )
    forbidden_activate = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/model-configs/{created.json()['id']}/activate",
        headers=auth_headers(other_token),
    )
    other_list = client.get(
        f"/api/v1/workspaces/{other_workspace['id']}/model-configs",
        headers=auth_headers(other_token),
    )

    assert created.status_code == 201
    assert forbidden_activate.status_code == 404
    assert forbidden_activate.json()["detail"]["code"] == "model_config_not_found"
    assert other_list.status_code == 200
    assert other_list.json() == []


def test_active_model_config_controls_provider_pricing_and_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-run@example.com")
    token = login(client, "model-run@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"
    created = client.post(
        path,
        headers=auth_headers(token),
        json={
            "provider": "mock-admin",
            "model": "mock-admin-classifier",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.01,
            "completion_token_cost_per_1k": 0.02,
            "max_context_tokens": 32768,
            "active": True,
        },
    )
    assert created.status_code == 201

    prompt = "Classify this refund request."
    completion = "refund_request"
    response = MockModelProvider(db_session).complete(
        workspace_id=workspace_id,
        purpose="classification",
        language=SupportedLanguage.en,
        prompt=prompt,
        model="mock-cheap",
        completion_text=completion,
    )

    prompt_tokens = estimate_tokens(prompt, SupportedLanguage.en)
    completion_tokens = estimate_tokens(completion, SupportedLanguage.en)
    expected_cost = estimate_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_token_cost_per_1k=0.01,
        completion_token_cost_per_1k=0.02,
    )
    stored = db_session.scalar(select(AIRun).where(AIRun.id == response.ai_run.id))
    assert stored is not None
    assert stored.provider == "mock-admin"
    assert stored.model == "mock-admin-classifier"
    assert stored.model_config_id == UUID(created.json()["id"])
    assert stored.estimated_cost == expected_cost

    summary = client.get(
        f"/api/v1/workspaces/{workspace['id']}/costs/summary",
        headers=auth_headers(token),
    )
    assert summary.status_code == 200
    assert summary.json()["recent_ai_runs"][0]["model_config_id"] == created.json()["id"]


def test_active_model_config_context_limit_records_failed_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-limit@example.com")
    token = login(client, "model-limit@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "mock-limit",
            "model": "mock-tiny-context",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.01,
            "completion_token_cost_per_1k": 0.02,
            "max_context_tokens": 256,
            "active": True,
        },
    )
    assert created.status_code == 201

    try:
        MockModelProvider(db_session).complete(
            workspace_id=workspace_id,
            purpose="classification",
            language=SupportedLanguage.en,
            prompt="token " * 300,
            model="mock-cheap",
            completion_text="refund_request",
        )
    except MockModelProviderError as exc:
        assert "model_context_exceeded" in str(exc)
    else:
        raise AssertionError("expected model context error")

    stored = db_session.scalar(select(AIRun).where(AIRun.workspace_id == workspace_id))
    assert stored is not None
    assert stored.provider == "mock-limit"
    assert stored.model == "mock-tiny-context"
    assert stored.status == "failed"
    assert stored.error_message is not None
    assert "model_context_exceeded" in stored.error_message
    assert stored.estimated_cost == 0


def test_openai_compatible_provider_records_successful_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "openai-success@example.com")
    token = login(client, "openai-success@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "purpose": "draft_response",
            "prompt_token_cost_per_1k": 0.00015,
            "completion_token_cost_per_1k": 0.0006,
            "max_context_tokens": 8192,
            "active": True,
        },
    )
    assert created.status_code == 201
    transport = FakeOpenAITransport("Please request a refund within 30 days.")

    response = OpenAICompatibleModelProvider(
        db_session,
        api_key="sk-test",
        base_url="https://api.test/v1",
        timeout_seconds=7,
        transport=transport,
    ).complete(
        workspace_id=workspace_id,
        purpose="draft_response",
        language=SupportedLanguage.en,
        prompt="Draft a cited answer",
        model="mock-standard",
    )

    assert response.content == "Please request a refund within 30 days."
    assert transport.calls == [
        {
            "api_key": "sk-test",
            "base_url": "https://api.test/v1",
            "model": "gpt-4o-mini",
            "prompt": "Draft a cited answer",
            "timeout_seconds": 7,
        }
    ]
    stored = db_session.scalar(select(AIRun).where(AIRun.id == response.ai_run.id))
    assert stored is not None
    assert stored.provider == "openai"
    assert stored.model == "gpt-4o-mini"
    assert stored.status == "succeeded"
    assert stored.prompt_tokens == 42
    assert stored.completion_tokens == 11
    assert stored.total_tokens == 53
    assert stored.estimated_cost == estimate_cost(
        prompt_tokens=42,
        completion_tokens=11,
        prompt_token_cost_per_1k=0.00015,
        completion_token_cost_per_1k=0.0006,
    )


def test_openai_compatible_provider_records_missing_key_failure(
    client: TestClient, db_session: Session
) -> None:
    register(client, "openai-missing-key@example.com")
    token = login(client, "openai-missing-key@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "openai-compatible",
            "model": "company-chat-model",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.001,
            "completion_token_cost_per_1k": 0.002,
            "max_context_tokens": 4096,
            "active": True,
        },
    )
    assert created.status_code == 201
    transport = FakeOpenAITransport()

    try:
        OpenAICompatibleModelProvider(
            db_session, api_key="", base_url="https://api.test/v1", transport=transport
        ).complete(
            workspace_id=workspace_id,
            purpose="classification",
            language=SupportedLanguage.en,
            prompt="Classify this request",
            model="mock-cheap",
        )
    except ModelProviderError as exc:
        assert "openai_api_key_missing" in str(exc)
    else:
        raise AssertionError("expected missing API key failure")

    assert transport.calls == []
    stored = db_session.scalar(select(AIRun).where(AIRun.workspace_id == workspace_id))
    assert stored is not None
    assert stored.provider == "openai-compatible"
    assert stored.model == "company-chat-model"
    assert stored.status == "failed"
    assert stored.error_message is not None
    assert "openai_api_key_missing" in stored.error_message


def test_configured_provider_dispatches_openai_compatible_configs(
    client: TestClient, db_session: Session
) -> None:
    register(client, "configured-openai@example.com")
    token = login(client, "configured-openai@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])
    created = client.post(
        f"/api/v1/workspaces/{workspace['id']}/model-configs",
        headers=auth_headers(token),
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.00015,
            "completion_token_cost_per_1k": 0.0006,
            "max_context_tokens": 8192,
            "active": True,
        },
    )
    assert created.status_code == 201
    transport = FakeOpenAITransport("refund_request")
    openai_provider = OpenAICompatibleModelProvider(
        db_session, api_key="sk-test", base_url="https://api.test/v1", transport=transport
    )

    response = ConfiguredModelProvider(db_session, openai_provider=openai_provider).complete(
        workspace_id=workspace_id,
        purpose="classification",
        language=SupportedLanguage.en,
        prompt="Classify this refund request",
        model="mock-cheap",
    )

    assert response.content == "refund_request"
    assert transport.calls[0]["model"] == "gpt-4o-mini"
    stored = db_session.scalar(select(AIRun).where(AIRun.id == response.ai_run.id))
    assert stored is not None
    assert stored.provider == "openai"
    assert stored.model == "gpt-4o-mini"


def test_model_config_archive_owner_only_and_clears_agent_assignment(
    client: TestClient, db_session: Session
) -> None:
    register(client, "model-lifecycle-owner@example.com")
    owner_token = login(client, "model-lifecycle-owner@example.com")
    workspace = create_workspace(client, owner_token)
    member = register(client, "model-lifecycle-member@example.com")
    member_token = login(client, "model-lifecycle-member@example.com")
    add_member(db_session, workspace_id=workspace["id"], user_id=member["id"])
    path = f"/api/v1/workspaces/{workspace['id']}/model-configs"

    member_create = client.post(
        path,
        headers=auth_headers(member_token),
        json={
            "provider": "mock",
            "model": "member-model",
            "purpose": "classification",
            "prompt_token_cost_per_1k": 0.001,
            "completion_token_cost_per_1k": 0.002,
            "max_context_tokens": 4096,
            "active": True,
        },
    )
    assert member_create.status_code == 403
    assert member_create.json()["detail"]["code"] == "workspace_permission_required"
    assert member_create.json()["detail"]["required_permission"] == "models:write"

    created = client.post(
        path,
        headers=auth_headers(owner_token),
        json={
            "provider": "mock-admin",
            "model": "archive-me",
            "purpose": "draft_response",
            "prompt_token_cost_per_1k": 0.001,
            "completion_token_cost_per_1k": 0.002,
            "max_context_tokens": 8192,
            "active": True,
        },
    )
    assert created.status_code == 201
    agent = client.post(
        f"/api/v1/workspaces/{workspace['id']}/agents",
        headers=auth_headers(owner_token),
        json={
            "name": "Model archive agent",
            "token_budget": 4000,
            "model_config_id": created.json()["id"],
        },
    )
    assert agent.status_code == 201
    assert agent.json()["model_config_id"] == created.json()["id"]

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
    assert activate_archived.json()["detail"]["code"] == "model_config_not_found"

    stored_agent = db_session.scalar(
        select(AgentConfig).where(AgentConfig.id == UUID(agent.json()["id"]))
    )
    assert stored_agent is not None
    assert stored_agent.model_config_id is None
    stored_config = db_session.scalar(
        select(ModelConfig).where(ModelConfig.id == UUID(created.json()["id"]))
    )
    assert stored_config is not None
    assert stored_config.archived_at is not None
