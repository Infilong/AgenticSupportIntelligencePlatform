from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.retrieval import RetrievalTrace, RetrievedChunk
from app.services.lexical_search import lexical_score


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


def upload_document(
    client: TestClient,
    token: str,
    workspace_id: str,
    *,
    title: str,
    language: str,
    content: str,
) -> dict:
    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/knowledge-documents",
        headers=auth_headers(token),
        json={
            "title": title,
            "content_type": "text/plain",
            "language": language,
            "content": content,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_lexical_score_supports_english_and_cjk() -> None:
    assert (
        lexical_score(
            "refund within 30 days",
            "Refunds are available within 30 days.",
            SupportedLanguage.en,
        )
        > 0.5
    )
    assert (
        lexical_score(
            "返金30日以内",
            "返金は購入から30日以内に申請できます。",
            SupportedLanguage.ja,
        )
        > 0.2
    )
    assert lexical_score("退款30天", "购买后30天内可以申请退款。", SupportedLanguage.zh) > 0.2
    assert lexical_score("refund", "Password reset policy", SupportedLanguage.en) == 0.0


def test_retrieval_returns_cited_chunks_and_persists_trace(
    client: TestClient, db_session: Session
) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(
        client,
        token,
        workspace["id"],
        title="Refund Policy",
        language="en",
        content="Refunds are available within 30 days after purchase. " * 30,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/retrieval/search",
        headers=auth_headers(token),
        json={"query": "refund within 30 days", "language": "en", "top_k": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "lexical"
    assert body["no_source"] is False
    assert body["results"]
    top = body["results"][0]
    assert top["document_title"] == "Refund Policy"
    assert "Refund Policy v1 #chunk-" in top["citation"]
    assert top["vector_score"] is None
    assert top["combined_score"] == top["lexical_score"]

    trace = db_session.scalar(
        select(RetrievalTrace).where(RetrievalTrace.id == UUID(body["trace_id"]))
    )
    assert trace is not None
    assert trace.workspace_id == UUID(workspace["id"])
    assert trace.no_source is False
    stored = db_session.scalars(
        select(RetrievedChunk).where(RetrievedChunk.retrieval_trace_id == trace.id)
    ).all()
    assert len(stored) == len(body["results"])


def test_retrieval_language_and_document_filters(client: TestClient) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    refund_doc = upload_document(
        client,
        token,
        workspace["id"],
        title="Refund Policy JA",
        language="ja",
        content="返金は購入から30日以内に申請できます。" * 30,
    )
    upload_document(
        client,
        token,
        workspace["id"],
        title="Billing Policy EN",
        language="en",
        content="Invoices are issued monthly for paid plans. " * 30,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/retrieval/search",
        headers=auth_headers(token),
        json={
            "query": "返金30日以内",
            "language": "ja",
            "top_k": 5,
            "document_id": refund_doc["document"]["id"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["no_source"] is False
    assert {result["document_title"] for result in body["results"]} == {"Refund Policy JA"}
    assert {result["language"] for result in body["results"]} == {"ja"}


def test_retrieval_no_source_still_stores_trace(client: TestClient, db_session: Session) -> None:
    register(client, "owner@example.com")
    token = login(client, "owner@example.com")
    workspace = create_workspace(client, token)
    upload_document(
        client,
        token,
        workspace["id"],
        title="Refund Policy",
        language="en",
        content="Refunds are available within 30 days after purchase. " * 20,
    )

    response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/retrieval/search",
        headers=auth_headers(token),
        json={"query": "delete account permanently", "language": "en", "min_score": 0.6},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["no_source"] is True
    assert body["results"] == []
    trace = db_session.scalar(
        select(RetrievalTrace).where(RetrievalTrace.id == UUID(body["trace_id"]))
    )
    assert trace is not None
    assert trace.no_source is True


def test_retrieval_does_not_leak_other_workspace_chunks(client: TestClient) -> None:
    register(client, "owner@example.com")
    owner_token = login(client, "owner@example.com")
    owner_workspace = create_workspace(client, owner_token, "Owner Workspace")
    upload_document(
        client,
        owner_token,
        owner_workspace["id"],
        title="Private Refund Policy",
        language="en",
        content="Secret enterprise refunds are available within 30 days. " * 20,
    )

    register(client, "other@example.com")
    other_token = login(client, "other@example.com")
    other_workspace = create_workspace(client, other_token, "Other Workspace")

    response = client.post(
        f"/api/v1/workspaces/{other_workspace['id']}/retrieval/search",
        headers=auth_headers(other_token),
        json={"query": "secret enterprise refunds 30 days", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["no_source"] is True
    assert body["results"] == []


def test_retrieval_rejects_unauthenticated_requests(client: TestClient) -> None:
    response = client.post(
        "/api/v1/workspaces/00000000-0000-0000-0000-000000000000/retrieval/search",
        json={"query": "refund", "language": "en"},
    )

    assert response.status_code == 401
