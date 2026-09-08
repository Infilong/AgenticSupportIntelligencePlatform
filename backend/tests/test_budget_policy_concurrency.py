"""First-use Costs, policy reads and embedding admission must share one policy."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, local

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.models.budget import WorkspaceBudgetPolicy
from app.services.budget_policy_service import BudgetPolicyService
from app.services.embedding_attempts import EmbeddingAttemptLedger

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


@pytest.mark.parametrize("competing_operation", ["policy", "embedding"])
def test_first_use_policy_creation_is_serialized(review_database, competing_operation):
    engine, ids = review_database
    first_reads = Barrier(2)
    thread = local()

    def synchronize_missing_reads(connection, cursor, statement, parameters, context, many):
        # Force both initial SELECTs to observe absence before either caller inserts.
        if "FROM workspace_budget_policies" in statement and not getattr(thread, "read", False):
            thread.read = True
            first_reads.wait(timeout=10)

    def read_policy():
        with Session(engine) as db:
            return BudgetPolicyService(db).get_or_create(workspace_id=ids[0]).id

    def compete():
        if competing_operation == "policy":
            return read_policy()
        return EmbeddingAttemptLedger(engine).begin(workspace_id=ids[0], language="en",
            model="text-embedding-3-small", texts=["test"], token_cost_per_1k=0.001,
            purpose="embedding_query")

    event.listen(engine, "after_cursor_execute", synchronize_missing_reads)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(read_policy)
            second = pool.submit(compete)
            policy_id, competing_id = first.result(timeout=15), second.result(timeout=15)
    finally:
        event.remove(engine, "after_cursor_execute", synchronize_missing_reads)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(WorkspaceBudgetPolicy)) == 1
        policy = db.scalar(select(WorkspaceBudgetPolicy))
        assert policy.id == policy_id
        assert policy.monthly_token_budget == 100_000
        if competing_operation == "policy":
            assert competing_id == policy_id
