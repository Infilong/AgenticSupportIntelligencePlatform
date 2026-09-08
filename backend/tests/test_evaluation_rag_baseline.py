import json
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_evaluations import auth_headers, create_workspace, login, register
from test_retrieval import upload_document

from app.models.ai import AIRun
from app.models.retrieval import RetrievalTrace
from app.services.embedding_provider import MockEmbeddingProvider


@pytest.mark.parametrize("language,policy", [
    ("en", "Refunds are allowed within 7 days."),
    ("ja", "返金は購入から7日以内に申請できます。"),
    ("zh", "购买后7天内可以申请退款。"),
])
def test_rag_baseline_follows_policy_and_ledgers_generation(
    client: TestClient, db_session: Session, monkeypatch, language, policy,
):
    # Control similarity, not semantic quality; this is a deterministic generation-contract test.
    monkeypatch.setattr(MockEmbeddingProvider, "embed_texts",
                        lambda self, texts: [[1.0] * 16 for _ in texts])
    register(client, "rag-baseline@example.com")
    token = login(client, "rag-baseline@example.com")
    workspace = create_workspace(client, token)
    upload_document(client, token, workspace["id"], title="Current policy",
                    language=language, content=policy * 20)
    response = client.post(f"/api/v1/workspaces/{workspace['id']}/evaluations",
                           headers=auth_headers(token), json={
        "name": "Evidence baseline", "modes": ["vector_rag"],
        "jsonl_cases": json.dumps({"id": "policy", "language": language,
                                   "input_message": policy, "expected_route": "finalize"}),
    })
    assert response.status_code == 201
    result = response.json()["results"][0]
    assert policy in result["answer"]
    obsolete_policy = {"en": "30 days", "ja": "30日", "zh": "30天"}[language]
    assert obsolete_policy not in result["answer"]
    assert json.loads(result["citations_json"])
    ledger = db_session.scalar(select(AIRun).where(
        AIRun.workspace_id == UUID(workspace["id"]), AIRun.purpose == "evaluation_vector_rag",
    ))
    assert ledger is not None
    assert result["prompt_tokens"] == ledger.prompt_tokens > 0
    assert result["estimated_cost"] == ledger.estimated_cost > 0
    trace = db_session.scalar(select(RetrievalTrace).where(
        RetrievalTrace.workspace_id == UUID(workspace["id"]),
    ))
    assert trace.strategy == "vector"


def test_no_source_skips_generation(client: TestClient, db_session: Session):
    from app.core.language import SupportedLanguage
    from app.services.evaluation_rag_baseline import run_rag_baseline

    register(client, "empty-baseline@example.com")
    token = login(client, "empty-baseline@example.com")
    workspace = create_workspace(client, token)
    result = run_rag_baseline(db_session, workspace_id=UUID(workspace["id"]),
                              question="Refund policy?", language=SupportedLanguage.en)
    assert result.route == "human_review"
    assert result.answer is None
    assert db_session.scalar(select(AIRun)) is None


def test_evidence_packing_is_bounded():
    from app.services.evaluation_rag_baseline import pack_evidence

    sources = [SimpleNamespace(citation=f"source-{i}", content="x" * 10000) for i in range(10)]
    packed = pack_evidence(sources)
    assert sum(len(snippet) for _, snippet in packed) == 3200
    assert all(len(snippet) <= 800 for _, snippet in packed)
    assert len(packed) == 4


def test_vector_mode_does_not_use_lexical_score(db_session: Session):
    from app.core.language import SupportedLanguage
    from app.services.retrieval_service import RetrievalService

    candidate = SimpleNamespace(
        document=SimpleNamespace(id=uuid4(), title="Refund policy"),
        version=SimpleNamespace(version=1),
        chunk=SimpleNamespace(id=uuid4(), chunk_index=0, content="refund policy", token_count=2),
        embedding=SimpleNamespace(vector=[-1.0, 0.0]),
    )
    args = ("refund policy", [1.0, 0.0], SupportedLanguage.en, candidate)
    vector = RetrievalService(db_session, strategy="vector")._score_candidate(*args)
    hybrid = RetrievalService(db_session)._score_candidate(*args)
    assert vector.combined_score == vector.vector_score == 0
    assert vector.lexical_score is None
    assert hybrid.combined_score > vector.combined_score


@pytest.mark.parametrize("answer,accepted", [
    ("Unsupported answer without a source.", False),
    ("Seven days [Policy#chunk-0].", True),
    ("Seven days [Policy#chunk-0], repeated [Policy#chunk-0].", True),
    ("Seven days [Policy#chunk-0] and [Invented#chunk-9].", False),
    ("Seven days [Policy#chunk-01].", False),
    ("", False),
])
def test_provider_citations_match_packed_evidence(db_session: Session, monkeypatch,
                                                answer, accepted):
    from app.core.language import SupportedLanguage
    from app.services.budgeted_model_provider import BudgetedModelProvider
    from app.services.evaluation_rag_baseline import run_rag_baseline
    from app.services.retrieval_service import RetrievalService

    monkeypatch.setattr(RetrievalService, "search", lambda *args, **kwargs: SimpleNamespace(
        results=[SimpleNamespace(citation="[Policy#chunk-0]", content="Seven-day policy")]))
    calls = []

    def complete(self, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=answer,
                               ai_run=SimpleNamespace(prompt_tokens=50, estimated_cost=0.001))

    monkeypatch.setattr(BudgetedModelProvider, "complete", complete)
    result = run_rag_baseline(db_session, workspace_id=uuid4(), question="Refund?",
                              language=SupportedLanguage.en)
    assert "Seven-day policy" in calls[0]["prompt"]
    assert result.answer == answer
    assert result.citations == (["[Policy#chunk-0]"] if accepted else [])
    assert result.route == ("finalize" if accepted else "human_review")
    assert result.prompt_tokens == 50
    assert result.estimated_cost == 0.001
