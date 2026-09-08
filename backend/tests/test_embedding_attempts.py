import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_embedding_api import StubTransport
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus
from app.models.budget import WorkspaceBudgetPolicy
from app.models.knowledge import DocumentStatus, KnowledgeDocument
from app.models.workspace import Workspace
from app.services.accounted_embeddings import AccountedEmbeddingProvider
from app.services.embedding_api import EmbeddingAPI
from app.services.embedding_attempts import EmbeddingAdmissionError, EmbeddingAttemptLedger
from app.services.embedding_transport import EmbeddingTransportError

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def begin(ledger, workspace_id):
    return ledger.begin(workspace_id=workspace_id, language=SupportedLanguage.en,
        model="text-embedding-3-small", texts=["refund policy"], token_cost_per_1k=0.001,
        purpose="embedding_document")


def test_ledger_does_not_commit_outer_document_transaction(review_database):
    engine, ids = review_database
    ledger = EmbeddingAttemptLedger(engine)
    with Session(engine) as outer:
        document = KnowledgeDocument(workspace_id=ids[0], title="Pending document",
            language=SupportedLanguage.en, status=DocumentStatus.indexing,
            created_by_user_id=ids[2][0])
        outer.add(document)
        outer.flush()
        document_id = document.id
        attempt_id = begin(ledger, ids[0])
        ledger.finish(workspace_id=ids[0], attempt_id=attempt_id, prompt_tokens=3, latency_ms=12)
        outer.rollback()
    with Session(engine) as db:
        assert db.get(KnowledgeDocument, document_id) is None
        attempt = db.get(AIRun, attempt_id)
        assert attempt.status == AIRunStatus.succeeded
        assert attempt.total_tokens == 3
        assert attempt.estimated_cost == pytest.approx(0.000003)


def test_pending_and_uncertain_usage_stays_reserved(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        db.add(WorkspaceBudgetPolicy(workspace_id=ids[0], monthly_token_budget=20))
        db.commit()
    ledger = EmbeddingAttemptLedger(engine)
    attempt_id = begin(ledger, ids[0])
    for reconcile in (False, True):
        if reconcile:
            ledger.finish(workspace_id=ids[0], attempt_id=attempt_id,
                          prompt_tokens=None, latency_ms=12)
        with pytest.raises(EmbeddingAdmissionError, match="monthly_token_budget"):
            begin(ledger, ids[0])
    with pytest.raises(EmbeddingAdmissionError, match="already finalized"):
        ledger.finish(workspace_id=ids[0], attempt_id=attempt_id, prompt_tokens=1, latency_ms=1)


def test_concurrent_admission_cannot_overspend(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        db.add(WorkspaceBudgetPolicy(workspace_id=ids[0], monthly_token_budget=20))
        db.commit()

    def reserve():
        try:
            begin(EmbeddingAttemptLedger(engine), ids[0])
            return "admitted"
        except EmbeddingAdmissionError:
            return "denied"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: reserve(), range(2))) == ["admitted", "denied"]


def test_foreign_workspace_cannot_finalize_attempt(review_database):
    engine, ids = review_database
    ledger = EmbeddingAttemptLedger(engine)
    attempt_id = begin(ledger, ids[0])
    with pytest.raises(EmbeddingAdmissionError, match="not found"):
        ledger.finish(workspace_id=uuid4(), attempt_id=attempt_id, prompt_tokens=1, latency_ms=1)
    with Session(engine) as db:
        assert db.get(AIRun, attempt_id).status == AIRunStatus.pending


@pytest.mark.parametrize("failure", [False, True])
def test_accounted_dispatch_records_success_or_unknown_usage(review_database, failure, monkeypatch):
    engine, ids = review_database
    stub = StubTransport(payload={"model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 2, "total_tokens": 2},
        "data": [{"index": 0, "embedding": [0.25, 0.5]}]},
        error=EmbeddingTransportError("embedding_http_503") if failure else None)
    provider = AccountedEmbeddingProvider(
        api=EmbeddingAPI(api_key="synthetic", model="text-embedding-3-small",
                         dimensions=2, transport=stub),
        ledger=EmbeddingAttemptLedger(engine), workspace_id=ids[0], language=SupportedLanguage.en,
        token_cost_per_1k=0.001, purpose="embedding_query")
    original = stub.create

    def observed(**kwargs):
        with Session(engine) as observer:
            assert observer.scalar(select(AIRun)).status == AIRunStatus.pending
            # Provider I/O occurs after the budget lock is released.
            observer.scalar(select(Workspace).where(Workspace.id == ids[0])
                            .with_for_update(nowait=True))
        return original(**kwargs)

    monkeypatch.setattr(stub, "create", observed)
    if failure:
        with pytest.raises(EmbeddingTransportError):
            provider.embed_texts(["refund policy"])
    else:
        assert provider.embed_texts(["refund policy"]) == [[0.25, 0.5]]
    assert len(stub.calls) == 1
    with Session(engine) as db:
        attempt = db.scalar(select(AIRun))
        assert attempt.status == (AIRunStatus.uncertain if failure else AIRunStatus.succeeded)
        assert attempt.total_tokens == (13 if failure else 2)
        assert len(attempt.rendered_prompt_hash) == 64
