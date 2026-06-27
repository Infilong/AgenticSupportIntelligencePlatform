from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus, CacheEntry
from app.services.model_provider import MockModelProvider, MockModelProviderError
from app.services.token_accounting import estimate_cost, estimate_tokens
from app.services.token_budget import TokenBudgetPlanner


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


def test_token_estimator_and_cost_calculator_are_deterministic() -> None:
    assert estimate_tokens("Refunds are available within 30 days.", SupportedLanguage.en) == 7
    assert estimate_tokens("返金は30日以内です。", SupportedLanguage.ja) >= 5
    assert estimate_cost(
        prompt_tokens=1000,
        completion_tokens=500,
        prompt_token_cost_per_1k=0.001,
        completion_token_cost_per_1k=0.002,
    ) == 0.002


def test_token_budget_planner_selects_cheaper_model_and_denies_over_budget() -> None:
    planner = TokenBudgetPlanner()

    classification = planner.plan(
        purpose="classification",
        estimated_context_tokens=500,
        requested_completion_tokens=50,
        max_total_tokens=2000,
        max_estimated_cost=0.01,
    )
    too_large = planner.plan(
        purpose="final_answer",
        estimated_context_tokens=9000,
        requested_completion_tokens=1000,
        max_total_tokens=8000,
        max_estimated_cost=10.0,
    )
    too_expensive = planner.plan(
        purpose="final_answer",
        estimated_context_tokens=7000,
        requested_completion_tokens=500,
        max_total_tokens=9000,
        max_estimated_cost=0.0001,
    )

    assert classification.selected_model == "mock-cheap"
    assert classification.allowed is True
    assert too_large.allowed is False
    assert too_large.reason == "token_budget_exceeded"
    assert too_large.compression_required is True
    assert too_expensive.allowed is False
    assert too_expensive.route_to_human_review is True
    assert too_expensive.reason == "cost_budget_exceeded"


def test_mock_model_provider_records_successful_ai_run(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    response = MockModelProvider(db_session).complete(
        workspace_id=UUID(workspace["id"]),
        purpose="classification",
        language=SupportedLanguage.en,
        prompt="Classify this refund request.",
        model="mock-cheap",
        completion_text="refund_request",
    )

    assert response.content == "refund_request"
    assert response.ai_run.status == AIRunStatus.succeeded
    assert response.ai_run.prompt_tokens > 0
    assert response.ai_run.completion_tokens > 0
    assert response.ai_run.total_tokens == (
        response.ai_run.prompt_tokens + response.ai_run.completion_tokens
    )
    stored = db_session.scalar(select(AIRun).where(AIRun.id == response.ai_run.id))
    assert stored is not None
    assert stored.workspace_id == UUID(workspace["id"])


def test_mock_model_provider_records_failed_ai_run(client: TestClient, db_session: Session) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)

    with pytest.raises(MockModelProviderError):
        MockModelProvider(db_session).complete(
            workspace_id=UUID(workspace["id"]),
            purpose="final_answer",
            language=SupportedLanguage.en,
            prompt="Draft a support response.",
            fail=True,
        )

    stored = db_session.scalar(select(AIRun).where(AIRun.workspace_id == UUID(workspace["id"])))
    assert stored is not None
    assert stored.status == AIRunStatus.failed
    assert stored.error_message == "mock provider failure"
    assert stored.completion_tokens == 0


def test_cost_summary_is_workspace_scoped(client: TestClient, db_session: Session) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    register(client, "other@example.com")
    other_token = login(client, "other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    provider = MockModelProvider(db_session)
    provider.complete(
        workspace_id=UUID(owner_workspace["id"]),
        purpose="classification",
        language=SupportedLanguage.en,
        prompt="Classify refund request.",
        model="mock-cheap",
        completion_text="refund_request",
    )
    provider.complete(
        workspace_id=UUID(owner_workspace["id"]),
        purpose="final_answer",
        language=SupportedLanguage.en,
        prompt="Draft response.",
        model="mock-standard",
        completion_text="Refunds are available within 30 days.",
        cache_hit=True,
    )
    provider.complete(
        workspace_id=UUID(other_workspace["id"]),
        purpose="classification",
        language=SupportedLanguage.en,
        prompt="Classify billing request.",
        model="mock-cheap",
        completion_text="billing",
    )

    owner_summary = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/costs/summary",
        headers=auth_headers(owner_token),
    )
    forbidden = client.get(
        f"/api/v1/workspaces/{owner_workspace['id']}/costs/summary",
        headers=auth_headers(other_token),
    )

    assert owner_summary.status_code == 200
    body = owner_summary.json()
    assert body["total_runs"] == 2
    assert body["total_tokens"] > 0
    assert body["cache_hit_rate"] == 0.5
    assert {item["purpose"] for item in body["by_purpose"]} == {
        "classification",
        "final_answer",
    }
    assert forbidden.status_code == 404
    assert forbidden.json()["detail"]["code"] == "workspace_not_found"


def test_cache_entry_is_unique_by_workspace_key_and_purpose(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    workspace_id = UUID(workspace["id"])

    db_session.add(
        CacheEntry(
            workspace_id=workspace_id,
            cache_key="context:abc",
            purpose="context_compression",
            language=SupportedLanguage.en,
            value_json='{"summary": "cached"}',
            token_count=12,
        )
    )
    db_session.commit()
    db_session.add(
        CacheEntry(
            workspace_id=workspace_id,
            cache_key="context:abc",
            purpose="context_compression",
            language=SupportedLanguage.en,
            value_json='{"summary": "duplicate"}',
            token_count=12,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
