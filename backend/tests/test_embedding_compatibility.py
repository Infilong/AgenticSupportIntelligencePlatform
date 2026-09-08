from uuid import UUID

import pytest
from sqlalchemy import select
from test_retrieval import create_workspace, login, register, upload_document

from app.core.language import SupportedLanguage
from app.models.knowledge import Embedding
from app.services.embedding_provider import MockEmbeddingProvider
from app.services.retrieval_service import RetrievalError, RetrievalService


@pytest.fixture
def indexed_workspace(client, db_session):
    register(client, "embedding-contract@example.com")
    token = login(client, "embedding-contract@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"], title="Refund policy",
                    language="en", content="Refund policy allows returns within seven days.")
    return UUID(workspace["id"])


def search(db, workspace, provider, strategy="vector"):
    return RetrievalService(db, provider, strategy=strategy).search(
        workspace_id=workspace, query="Refund policy", language=SupportedLanguage.en,
        top_k=5, min_score=0, document_id=None,
    )


@pytest.mark.parametrize("field", ["provider", "model"])
def test_incompatible_model_is_excluded_before_query_dispatch(
    indexed_workspace, db_session, monkeypatch, field,
):
    embedding = db_session.scalar(select(Embedding))
    setattr(embedding, field, "different-embedding-space")
    db_session.commit()
    provider = MockEmbeddingProvider()

    def forbidden_call(texts):
        pytest.fail("No compatible candidates should mean no query embedding call")

    monkeypatch.setattr(provider, "embed_texts", forbidden_call)
    result = search(db_session, indexed_workspace, provider)
    assert result.no_source
    assert result.results == []
    # Lexical matching remains usable across an embedding configuration change.
    assert search(db_session, indexed_workspace, provider, "lexical").results


@pytest.mark.parametrize("vectors", [[], [[0.5]], [[float("nan")] * 16], [[0.0] * 16]])
def test_invalid_query_vectors_fail_explicitly(
    indexed_workspace, db_session, monkeypatch, vectors,
):
    provider = MockEmbeddingProvider()
    monkeypatch.setattr(provider, "embed_texts", lambda texts: vectors)
    with pytest.raises(RetrievalError, match="embedding"):
        search(db_session, indexed_workspace, provider)


def test_matching_embedding_space_returns_evidence(indexed_workspace, db_session):
    result = search(db_session, indexed_workspace, MockEmbeddingProvider())
    assert result.results
    assert result.results[0].citation


@pytest.mark.parametrize("vector", [[0.5], [0.0] * 16])
def test_invalid_stored_vectors_fail_before_query_dispatch(
    indexed_workspace, db_session, monkeypatch, vector,
):
    # Both stores permit these values; retrieval must enforce the configured dimensions.
    embedding = db_session.scalar(select(Embedding))
    embedding.vector = vector
    db_session.commit()
    provider = MockEmbeddingProvider()

    def forbidden_call(texts):
        pytest.fail("Corrupt stored embeddings must be rejected before provider dispatch")

    monkeypatch.setattr(provider, "embed_texts", forbidden_call)
    with pytest.raises(RetrievalError, match="embedding"):
        search(db_session, indexed_workspace, provider)
