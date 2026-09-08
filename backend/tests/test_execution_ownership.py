import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from test_review_transactions import review_database as review_database

from app.services.execution_ownership import (
    ExecutionBusy,
    ExecutionOwnershipLost,
    own_execution,
)

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def test_live_execution_excludes_recovery_but_other_execution_can_run(review_database):
    engine, ids = review_database
    execution = uuid4()
    with own_execution(engine, workspace_id=ids[0], execution_id=execution) as owner:
        owner.assert_owned()
        owner.connection.commit()
        with pytest.raises(ExecutionBusy):
            with own_execution(engine, workspace_id=ids[0], execution_id=execution):
                pytest.fail("live execution was stolen")
        with own_execution(engine, workspace_id=ids[0], execution_id=uuid4()) as other:
            other.assert_owned()
    with own_execution(engine, workspace_id=ids[0], execution_id=execution) as successor:
        successor.assert_owned()


def test_exception_releases_lock_before_connection_reuse(review_database):
    engine, ids = review_database
    execution = uuid4()
    with pytest.raises(ValueError, match="synthetic failure"):
        with own_execution(engine, workspace_id=ids[0], execution_id=execution):
            raise ValueError("synthetic failure")
    with own_execution(engine, workspace_id=ids[0], execution_id=execution) as owner:
        owner.assert_owned()


def test_terminated_owner_cannot_resume_and_successor_can_acquire(review_database):
    engine, ids = review_database
    execution = uuid4()
    with own_execution(engine, workspace_id=ids[0], execution_id=execution) as owner:
        with engine.begin() as control:
            # Terminate only the exact session created by this isolated test.
            assert control.scalar(text("SELECT pg_terminate_backend(:pid)"),
                                  {"pid": owner.backend_pid})
        with pytest.raises(DBAPIError):
            owner.assert_owned()
        with pytest.raises(ExecutionOwnershipLost):
            owner.assert_owned()
        with own_execution(engine, workspace_id=ids[0], execution_id=execution) as successor:
            successor.assert_owned()


def test_sqlite_cannot_claim_distributed_execution_ownership():
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(ValueError, match="PostgreSQL"):
            with own_execution(engine, workspace_id=uuid4(), execution_id=uuid4()):
                pytest.fail("unsupported ownership backend")
    finally:
        engine.dispose()
