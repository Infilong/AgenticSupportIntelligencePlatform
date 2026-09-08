import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session
from test_embedding_attempts import begin
from test_review_transactions import review_database as review_database

from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.budget import WorkspaceBudgetPolicy
from app.schemas.embedding_reconciliation import EmbeddingReconcileRequest
from app.services.embedding_attempts import EmbeddingAdmissionError, EmbeddingAttemptLedger
from app.services.embedding_reconciliation import ReconciliationError, reconcile_attempt

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def uncertain(engine, ids):
    ledger = EmbeddingAttemptLedger(engine)
    attempt_id = begin(ledger, ids[0])
    ledger.finish(workspace_id=ids[0], attempt_id=attempt_id, prompt_tokens=None, latency_ms=10)
    return attempt_id


def confirm(db, ids, attempt_id):
    return reconcile_attempt(db, workspace_id=ids[0], attempt_id=attempt_id, actor_id=ids[2][0],
        payload=EmbeddingReconcileRequest(confirmed_tokens=2, evidence_reference="case-1"))


def test_competing_reconciliation_only_commits_once(review_database):
    engine, ids = review_database
    attempt_id = uncertain(engine, ids)
    ready = Barrier(2)

    def worker(_):
        with Session(engine) as db:
            # Preload stale state to prove locked reads refresh the identity map.
            prior = db.get(AIRun, attempt_id)
            assert prior is not None
            ready.wait(timeout=10)
            try:
                confirm(db, ids, attempt_id)
                return "confirmed"
            except ReconciliationError as exc:
                assert exc.code == "embedding_attempt_not_uncertain"
                return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(worker, range(2))) == ["confirmed", "conflict"]
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "embedding_usage.reconciled")) == 1
        assert db.get(AIRun, attempt_id).total_tokens == 2


def test_audit_failure_rolls_back_usage_and_allows_retry(review_database):
    engine, ids = review_database
    attempt_id = uncertain(engine, ids)

    def reject_audit(connection, cursor, statement, parameters, context, many):
        if statement.startswith("INSERT INTO audit_logs"):
            raise RuntimeError("synthetic audit persistence failure")

    event.listen(engine, "before_cursor_execute", reject_audit)
    try:
        with Session(engine) as db, pytest.raises(RuntimeError, match="synthetic audit"):
            confirm(db, ids, attempt_id)
    finally:
        event.remove(engine, "before_cursor_execute", reject_audit)
    with Session(engine) as db:
        assert db.get(AIRun, attempt_id).status == AIRunStatus.uncertain
        assert db.get(AIRun, attempt_id).total_tokens == len("refund policy")
        assert db.scalar(select(func.count()).select_from(AuditLog)) == 0
        confirm(db, ids, attempt_id)


def test_confirmed_usage_releases_only_verified_budget(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        db.add(WorkspaceBudgetPolicy(workspace_id=ids[0], monthly_token_budget=20))
        db.commit()
    attempt_id = uncertain(engine, ids)
    ledger = EmbeddingAttemptLedger(engine)
    with pytest.raises(EmbeddingAdmissionError, match="monthly_token_budget"):
        begin(ledger, ids[0])
    with Session(engine) as db:
        confirm(db, ids, attempt_id)
    # Confirmed 2 tokens plus a new 13-token reservation fits, but a further 13 does not.
    begin(ledger, ids[0])
    with pytest.raises(EmbeddingAdmissionError, match="monthly_token_budget"):
        begin(ledger, ids[0])
