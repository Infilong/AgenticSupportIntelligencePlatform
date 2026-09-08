from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.language import SupportedLanguage
from app.services.lexical_search import lexical_score
from app.services.retrieval_service import RetrievalService
from tests.test_retrieval import create_workspace, login, register, upload_document


@pytest.mark.parametrize("query,content", [
    ("What is the refund policy?", "Refunds are available within 30 days after purchase."),
    ("refund policy", "Refund policies"),
    ("account", "Accounts"),
])
def test_english_plural_terms_preserve_relevant_support_matches(query, content):
    assert lexical_score(query, content, SupportedLanguage.en) >= 0.2


def test_plural_normalization_does_not_strip_double_s():
    assert lexical_score("address", "addres", SupportedLanguage.en) == 0


@pytest.mark.parametrize("language,query,content", [
    ("en", "refund", "Password reset policy"),
    ("ja", "返金期限", "端末設定手順"),
    ("zh", "退款期限", "密码重置步骤"),
])
def test_mock_vectors_cannot_make_unrelated_evidence_relevant(db_session, language, query, content):
    candidate = SimpleNamespace(
        chunk=SimpleNamespace(id=uuid4(), chunk_index=0, content=content, token_count=10),
        embedding=SimpleNamespace(vector=[1.0, 0.0]), version=SimpleNamespace(version=1),
        document=SimpleNamespace(id=uuid4(), title="Unrelated source"),
    )
    result = RetrievalService(db_session)._score_candidate(
        query, [1.0, 0.0], SupportedLanguage(language), candidate,
    )
    assert result.combined_score == 0
    assert result.lexical_score == 0
    assert result.vector_score is None


def test_default_mock_retrieval_never_calls_embedding_provider(client, db_session, monkeypatch):
    register(client, "lexical@example.test")
    token = login(client, "lexical@example.test")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"], title="Policy", language="en",
                    content="Refund deadline")
    service = RetrievalService(db_session)
    monkeypatch.setattr(service.embedding_provider, "embed_texts",
                        lambda texts: pytest.fail("Mock hash similarity must not rank evidence"))
    result = service.search(workspace_id=UUID(workspace["id"]), query="Refund deadline",
                            language=SupportedLanguage.en, top_k=4, min_score=0.2, document_id=None)
    assert result.strategy == "lexical"
    assert result.results[0].combined_score == 1
    assert result.results[0].vector_score is None
