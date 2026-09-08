import os
from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_embedding_runtime import configured_client as configured_client
from test_retrieval import auth_headers, create_workspace, login, register, upload_document
from test_review_transactions import review_database as review_database

from app.models.knowledge import Embedding
from app.models.retrieval import RetrievalTrace, RetrievedChunk
from app.services.embedding_transport import EmbeddingTransportError, OpenAIEmbeddingTransport

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def test_empty_search_is_successful_not_failed(configured_client):
    client, _ = configured_client
    register(client, "retrieval-empty@example.com")
    token = login(client, "retrieval-empty@example.com")
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/retrieval"
    response = client.post(base + "/search", headers=auth_headers(token),
                           json={"query": "Refund policy?", "language": "en"})
    assert response.status_code == 200 and response.json()["no_source"]
    trace = client.get(base + "/traces/" + response.json()["trace_id"],
                       headers=auth_headers(token)).json()
    assert trace["outcome"] == "succeeded" and trace["error_code"] is None


@pytest.mark.parametrize("failure", ["provider", "response", "stored_vector"])
def test_failed_search_persists_inspectable_scoped_trace(configured_client, monkeypatch, failure):
    client, engine = configured_client
    broken = False

    def transport(self, **kwargs):
        if broken and failure == "provider":
            raise EmbeddingTransportError("embedding_http_503")
        return {"model": kwargs["model"], "usage": {"prompt_tokens": 1, "total_tokens": 1},
                "data": [{"index": 0, "embedding": [] if broken and failure == "response"
                          else [1.0, 0.0, 0.0, 0.0]}]}

    monkeypatch.setattr(OpenAIEmbeddingTransport, "create", transport)
    register(client, "retrieval-failure@example.com")
    token = login(client, "retrieval-failure@example.com")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"], title="Policy", language="en",
                    content="Refunds within seven days.")
    broken = True
    if failure == "stored_vector":
        with Session(engine) as db:
            row = db.scalar(select(Embedding).where(
                Embedding.workspace_id == UUID(workspace["id"])))
            row.vector = [0.0] * 4
            db.commit()
    base = f"/api/v1/workspaces/{workspace['id']}/retrieval"
    response = client.post(base + "/search", headers=headers,
                           json={"query": "Refund policy?", "language": "en"})
    assert response.status_code == 400
    trace_id = response.json()["detail"]["trace_id"]
    assert trace_id
    # New request/session must find the failed trace after the error request has closed.
    trace_path = base + "/traces/" + trace_id
    trace = client.get(trace_path, headers=headers)
    assert trace.status_code == 200
    assert trace.json()["outcome"] == "failed"
    assert trace.json()["error_code"] == "embedding_failed"
    assert trace.json()["no_source"] and trace.json()["latency_ms"] > 0
    with Session(engine) as db:
        assert db.get(RetrievalTrace, UUID(trace_id)).outcome == "failed"
        assert not list(db.scalars(select(RetrievedChunk).where(
            RetrievedChunk.retrieval_trace_id == UUID(trace_id))))
    assert client.get(trace_path).status_code == 401
    other = create_workspace(client, token, "Other workspace")
    assert client.get(f"/api/v1/workspaces/{other['id']}/retrieval/traces/{trace_id}",
                      headers=headers).status_code == 404
    register(client, "retrieval-outsider@example.com")
    outsider = auth_headers(login(client, "retrieval-outsider@example.com"))
    assert client.get(trace_path, headers=outsider).status_code == 404
