import os
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_embedding_attempts import begin
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus
from app.services.accounted_embeddings import AccountedEmbeddingProvider
from app.services.embedding_api import EmbeddingAPI
from app.services.embedding_attempts import EmbeddingAdmissionError, EmbeddingAttemptLedger
from app.services.execution_ownership import ExecutionBusy, own_execution

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


@pytest.mark.parametrize("terminate", [False, True])
def test_dispatch_ownership_and_lost_owner_cannot_return_vectors(review_database, terminate):
    engine, ids = review_database

    class Transport:
        def create(self, **kwargs):
            with Session(engine) as db:
                attempt = db.scalar(select(AIRun))
                assert attempt.status == AIRunStatus.pending
                assert attempt.execution_protocol == "pg-session-v1"
                execution_id = attempt.execution_id
            with pytest.raises(ExecutionBusy):
                with own_execution(engine, workspace_id=ids[0], execution_id=execution_id):
                    pytest.fail("dispatch was not owned")
            with engine.begin() as control:
                if terminate:
                    # Locate the exact advisory owner of this isolated schema's sole attempt.
                    from hashlib import sha256
                    digest = sha256(ids[0].bytes + execution_id.bytes).digest()
                    keys = {"a": int.from_bytes(digest[:4], "big") & 0x7FFFFFFF,
                            "b": int.from_bytes(digest[4:8], "big") & 0x7FFFFFFF}
                    pid = control.scalar(text("SELECT pid FROM pg_locks WHERE locktype='advisory' "
                        "AND classid=:a AND objid=:b AND objsubid=2 AND granted"), keys)
                    assert pid is not None
                    assert control.scalar(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})
            return {"model": kwargs["model"], "usage": {"prompt_tokens": 2, "total_tokens": 2},
                    "data": [{"index": 0, "embedding": [0.5]}]}

    provider = AccountedEmbeddingProvider(
        api=EmbeddingAPI(api_key="synthetic", model="text-embedding-3-small", dimensions=1,
                         transport=Transport()), ledger=EmbeddingAttemptLedger(engine),
        workspace_id=ids[0], language=SupportedLanguage.en, token_cost_per_1k=0.001,
        purpose="embedding_document")
    if terminate:
        with pytest.raises(DBAPIError):
            provider.embed_texts(["refund policy"])
    else:
        assert provider.embed_texts(["refund policy"]) == [[0.5]]
    with Session(engine) as db:
        attempt = db.scalar(select(AIRun))
        assert attempt.status == (AIRunStatus.pending if terminate else AIRunStatus.succeeded)
        assert attempt.total_tokens == (13 if terminate else 2)


def test_owned_attempt_cannot_use_legacy_finalization(review_database):
    engine, ids = review_database
    ledger = EmbeddingAttemptLedger(engine)
    with ledger.execution(ids[0]) as owner:
        attempt = ledger.begin(workspace_id=ids[0], language=SupportedLanguage.en,
            model="text-embedding-3-small", texts=["refund"], token_cost_per_1k=0.001,
            purpose="embedding_document", owner=owner)
        with pytest.raises(EmbeddingAdmissionError, match="owner does not match"):
            ledger.finish(workspace_id=ids[0], attempt_id=attempt, prompt_tokens=1, latency_ms=1)
        ledger.finish(workspace_id=ids[0], attempt_id=attempt, prompt_tokens=1, latency_ms=1,
                      owner=owner)
    legacy = begin(ledger, ids[0])
    ledger.finish(workspace_id=ids[0], attempt_id=legacy, prompt_tokens=None, latency_ms=1)


def test_owner_rejects_foreign_scope_and_existing_transaction(review_database):
    engine, ids = review_database
    ledger = EmbeddingAttemptLedger(engine)
    with ledger.execution(ids[0]) as owner:
        params = dict(language=SupportedLanguage.en, model="text-embedding-3-small",
                      texts=["refund"], token_cost_per_1k=0.001,
                      purpose="embedding_document", owner=owner)
        with pytest.raises(EmbeddingAdmissionError, match="owner does not match"):
            ledger.begin(workspace_id=uuid4(), **params)
        owner.assert_owned()  # Starts a transaction outside the ledger's ownership.
        with pytest.raises(EmbeddingAdmissionError, match="clean transaction"):
            ledger.begin(workspace_id=ids[0], **params)
        owner.connection.rollback()
        with Session(engine) as db:
            assert db.scalar(select(AIRun)) is None
