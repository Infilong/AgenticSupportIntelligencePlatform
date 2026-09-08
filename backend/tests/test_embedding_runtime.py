import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_retrieval import auth_headers, create_workspace, login, register, upload_document
from test_review_transactions import review_database as review_database

from app.core.config import get_settings
from app.db.session import get_db
from app.main import create_app
from app.models.ai import AIRun, AIRunStatus
from app.models.knowledge import DocumentChunk, DocumentStatus, Embedding, KnowledgeDocument
from app.services.embedding_transport import EmbeddingTransportError, OpenAIEmbeddingTransport

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


@pytest.fixture
def configured_client(review_database, monkeypatch):
    engine, _ = review_database
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_DIMENSIONS", "4")
    monkeypatch.setenv("EMBEDDING_TOKEN_COST_PER_1K", "0.001")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-embedding-key")
    get_settings.cache_clear()
    app = create_app()

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        yield client, engine
    get_settings.cache_clear()


@pytest.mark.parametrize("language,policy,question,unrelated", [
    ("en", "Return eligible purchases within seven days.", "How can I obtain reimbursement?",
     "A musical instrument has strings."),
    ("ja", "購入後七日以内の商品を返品できます。", "返金手続きを教えて", "楽器の演奏方法"),
    ("zh", "购买后七日内可退货。", "怎样申请退款", "乐器演奏技巧"),
])
def test_configured_indexing_and_search_use_accounted_vectors(
    configured_client, monkeypatch, language, policy, question, unrelated,
):
    client, engine = configured_client
    calls = []

    def synthetic(self, **kwargs):
        calls.append(kwargs["texts"])
        return {"model": kwargs["model"],
            "usage": {"prompt_tokens": len(kwargs["texts"]), "total_tokens": len(kwargs["texts"])},
            "data": [{"index": index, "embedding":
                ([-1.0, 0.0, 0.0, 0.0] if text == unrelated else [1.0, 0.0, 0.0, 0.0])}
                for index, text in enumerate(kwargs["texts"])]}

    monkeypatch.setattr(OpenAIEmbeddingTransport, "create", synthetic)
    register(client, "semantic@example.com")
    token = login(client, "semantic@example.com")
    workspace = create_workspace(client, token)
    upload = upload_document(client, token, workspace["id"], title="Policy",
                             language=language, content=policy)
    upload_document(client, token, workspace["id"], title="Unrelated",
                    language=language, content=unrelated)
    path = f"/api/v1/workspaces/{workspace['id']}/retrieval/search"
    payload = {"query": question, "language": language, "top_k": 1, "min_score": 0.2}
    response = client.post(path, headers=auth_headers(token), json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["strategy"] == "hybrid"
    assert result["results"][0]["document_id"] == upload["document"]["id"]
    assert result["results"][0]["vector_score"] == 1
    assert result["results"][0]["citation"]
    assert len(calls) == 3
    register(client, "outsider@example.com")
    outsider = login(client, "outsider@example.com")
    assert client.post(path, headers=auth_headers(outsider), json=payload).status_code == 404
    assert client.post(path, json=payload).status_code == 401
    assert len(calls) == 3
    with Session(engine) as db:
        embeddings = db.scalars(select(Embedding).where(
            Embedding.workspace_id == UUID(workspace["id"]))).all()
        assert len(embeddings) == 2
        assert all(row.provider == "openai" and len(row.vector) == 4 for row in embeddings)
        runs = db.scalars(select(AIRun).where(AIRun.workspace_id == UUID(workspace["id"]))).all()
        assert len(runs) == 3
        assert all(row.status == AIRunStatus.succeeded and row.total_tokens == 1 for row in runs)
        assert {row.purpose for row in runs} == {"embedding_document", "embedding_query"}


def test_failed_configured_upload_is_explicit_and_usage_survives(configured_client, monkeypatch):
    client, engine = configured_client

    def unavailable(self, **kwargs):
        raise EmbeddingTransportError("embedding_http_503")

    monkeypatch.setattr(OpenAIEmbeddingTransport, "create", unavailable)
    register(client, "failed-index@example.com")
    token = login(client, "failed-index@example.com")
    workspace = create_workspace(client, token)
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/knowledge-documents",
        headers=auth_headers(token), json={"title": "Policy", "language": "en",
            "content_type": "text/plain", "content": "Refund policy"})
    assert response.status_code == 400
    with Session(engine) as db:
        document = db.scalar(select(KnowledgeDocument).where(
            KnowledgeDocument.workspace_id == UUID(workspace["id"])))
        assert document.status == DocumentStatus.failed
        assert "embedding_http_503" in document.error_message
        assert db.scalar(select(DocumentChunk).where(
            DocumentChunk.workspace_id == UUID(workspace["id"]))) is None
        attempt = db.scalar(select(AIRun).where(AIRun.workspace_id == UUID(workspace["id"])))
        assert attempt.status == AIRunStatus.uncertain
        assert attempt.total_tokens == len(b"Refund policy")
