import hashlib
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.services.model_provider import MockModelProvider, MockModelProviderError


def _workspace_id(client: TestClient, email: str) -> UUID:
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
    workspace = client.post(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"name": "Prompt Provenance Workspace"},
    )
    assert workspace.status_code == 201
    return UUID(workspace.json()["id"])


def test_successful_ai_run_hashes_exact_rendered_prompt(
    client: TestClient, db_session: Session
) -> None:
    prompt = "System: active prompt v2\nHuman: Can I get a refund?"
    response = MockModelProvider(db_session).complete(
        workspace_id=_workspace_id(client, "prompt-hash-success@example.com"),
        purpose="classification",
        language=SupportedLanguage.en,
        prompt=prompt,
        completion_text="refund_request",
    )

    assert response.ai_run.rendered_prompt_hash == hashlib.sha256(
        prompt.encode("utf-8")
    ).hexdigest()


def test_failed_ai_run_hashes_exact_rendered_prompt(
    client: TestClient, db_session: Session
) -> None:
    prompt = "System: active prompt v3\nHuman: unsafe request"

    with pytest.raises(MockModelProviderError) as raised:
        MockModelProvider(db_session).complete(
            workspace_id=_workspace_id(client, "prompt-hash-failure@example.com"),
            purpose="classification",
            language=SupportedLanguage.en,
            prompt=prompt,
            fail=True,
        )

    assert raised.value.ai_run is not None
    assert raised.value.ai_run.rendered_prompt_hash == hashlib.sha256(
        prompt.encode("utf-8")
    ).hexdigest()
