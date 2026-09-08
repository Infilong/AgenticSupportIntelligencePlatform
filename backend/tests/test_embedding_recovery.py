import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.embedding_attempts import EmbeddingAttemptLedger
from app.services.embedding_reconciliation import ReconciliationError
from app.services.embedding_recovery import recover_attempt

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def setup(engine, ids):
    with Session(engine) as db:
        db.add(WorkspaceMember(workspace_id=ids[0], user_id=ids[2][0], role=WorkspaceRole.owner))
        db.commit()
    return EmbeddingAttemptLedger(engine)


def begin(ledger, ids, owner):
    return ledger.begin(workspace_id=ids[0], language=SupportedLanguage.en,
        model="text-embedding-3-small", texts=["refund policy"], token_cost_per_1k=0.001,
        purpose="embedding_query", owner=owner)


def recover(db, ids, attempt):
    return recover_attempt(db, workspace_id=ids[0], attempt_id=attempt,
                           actor_id=ids[2][0], reason="Interrupted worker investigated")


def test_live_owner_is_rejected_orphan_is_audited_without_releasing_usage(review_database):
    engine, ids = review_database
    ledger = setup(engine, ids)
    with ledger.execution(ids[0]) as owner:
        attempt = begin(ledger, ids, owner)
        with Session(engine) as db, pytest.raises(ReconciliationError, match="execution_live"):
            recover(db, ids, attempt)
    with Session(engine) as db:
        recovered = recover(db, ids, attempt)
        assert recovered.status == AIRunStatus.uncertain
        assert recovered.total_tokens == 13
        assert recovered.estimated_cost == pytest.approx(0.000013)
        assert recovered.execution_id is not None
        with pytest.raises(ReconciliationError, match="not_pending"):
            recover(db, ids, attempt)
    with Session(engine) as db:
        audits = list(db.scalars(select(AuditLog).where(
            AuditLog.action == "embedding_execution.recovered")))
        assert len(audits) == 1
        assert audits[0].actor_user_id == ids[2][0]


def test_audit_failure_rolls_back_orphan_transition_and_can_retry(review_database):
    engine, ids = review_database
    ledger = setup(engine, ids)
    with ledger.execution(ids[0]) as owner:
        attempt = begin(ledger, ids, owner)

    def fail(*args):
        raise RuntimeError("synthetic audit failure")

    event.listen(AuditLog, "before_insert", fail)
    try:
        with Session(engine) as db, pytest.raises(RuntimeError, match="audit failure"):
            recover(db, ids, attempt)
    finally:
        event.remove(AuditLog, "before_insert", fail)
    with Session(engine) as db:
        assert db.get(AIRun, attempt).status == AIRunStatus.pending
        assert recover(db, ids, attempt).status == AIRunStatus.uncertain


def test_membership_is_rechecked_and_legacy_attempts_are_not_guessed(review_database):
    engine, ids = review_database
    ledger = setup(engine, ids)
    with ledger.execution(ids[0]) as owner:
        attempt = begin(ledger, ids, owner)
    with Session(engine) as db:
        member = db.scalar(select(WorkspaceMember))
        member.role = WorkspaceRole.viewer
        db.commit()
        with pytest.raises(ReconciliationError, match="forbidden"):
            recover(db, ids, attempt)
        assert db.get(AIRun, attempt).status == AIRunStatus.pending
    legacy = begin(ledger, ids, None)
    with Session(engine) as db, pytest.raises(ReconciliationError, match="unsupported"):
        recover(db, ids, legacy)


def test_concurrent_recovery_records_only_one_transition(review_database):
    engine, ids = review_database
    ledger = setup(engine, ids)
    with ledger.execution(ids[0]) as owner:
        attempt = begin(ledger, ids, owner)
    ready = Barrier(2)

    def request():
        with Session(engine) as db:
            ready.wait(timeout=5)
            try:
                return str(recover(db, ids, attempt).status)
            except ReconciliationError as error:
                return error.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert results.count("uncertain") == 1
    assert next(value for value in results if value != "uncertain") in {
        "embedding_execution_live", "embedding_attempt_not_pending",
    }
    with Session(engine) as db:
        assert len(list(db.scalars(select(AuditLog).where(
            AuditLog.action == "embedding_execution.recovered")))) == 1
        assert db.get(AIRun, attempt).total_tokens == 13
