import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier, Event
from uuid import uuid4

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.agent import AgentConfig, GraphRun, GraphRunStatus
from app.models.budget import WorkspaceBudgetPolicy
from app.models.reservation import ModelCallReservation
from app.models.workspace import Workspace
from app.services.budget_reservations import BudgetReservationDenied, BudgetReservationService
from app.services.model_provider import MockModelProvider
from app.services.token_budget import ModelCallBudgetPlan

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def plan(tokens=100, cost=0.001, allowed=True):
    return ModelCallBudgetPlan(allowed, "mock", "mock-cheap", tokens, 0, tokens,
                               4096, cost, False, not allowed)


def reserve(db, ids, **kwargs):
    return BudgetReservationService(db).reserve(workspace_id=ids[0], graph_run_id=ids[3],
                                                purpose="classification", plan=plan(**kwargs))


@pytest.mark.parametrize("field,value,reason", [
    ("per_run_token_budget", 50, "token_budget_exceeded"),
    ("per_run_cost_budget", 0.0001, "cost_budget_exceeded"),
    ("monthly_token_budget", 50, "monthly_token_budget_exceeded"),
    ("monthly_cost_budget", 0.0001, "monthly_cost_budget_exceeded"),
])
def test_each_policy_limit_denies_and_records_reason(review_database, field, value, reason):
    engine, ids = review_database
    with Session(engine) as db:
        policy = WorkspaceBudgetPolicy(workspace_id=ids[0])
        setattr(policy, field, value)
        db.add(policy)
        db.commit()
        with pytest.raises(BudgetReservationDenied, match=reason):
            reserve(db, ids)
        row = db.scalar(select(ModelCallReservation))
        assert row.status == "denied" and row.denial_reason == reason


def test_context_limit_and_agent_limit(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        with pytest.raises(BudgetReservationDenied, match="model_context_exceeded"):
            reserve(db, ids, allowed=False)
        with pytest.raises(BudgetReservationDenied, match="token_budget_exceeded"):
            reserve(db, ids, tokens=4001)


def test_expired_unresolved_reservations_count_until_explicit_release(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        first = reserve(db, ids, tokens=3000)
        with pytest.raises(BudgetReservationDenied, match="token_budget_exceeded"):
            reserve(db, ids, tokens=2000)
        first.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
        with pytest.raises(BudgetReservationDenied, match="token_budget_exceeded"):
            reserve(db, ids, tokens=2000)
        BudgetReservationService(db).finalize(workspace_id=ids[0], reservation_id=first.id)
        second = reserve(db, ids, tokens=2000)
        BudgetReservationService(db).finalize(workspace_id=ids[0], reservation_id=second.id)
        assert reserve(db, ids, tokens=3000).status == "reserved"


def test_consumed_reservation_uses_actual_ledger_without_double_counting(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        reservation = reserve(db, ids, tokens=3900)
        response = MockModelProvider(db).complete(
            workspace_id=ids[0], graph_run_id=ids[3], purpose="classification",
            language=SupportedLanguage.en, prompt="Hello", completion_text="Yes",
        )
        service = BudgetReservationService(db)
        service.finalize(workspace_id=ids[0], reservation_id=reservation.id,
                         ai_run_id=response.ai_run.id)
        assert reserve(db, ids, tokens=3998).status == "reserved"
        with pytest.raises(BudgetReservationDenied, match="token_budget_exceeded"):
            reserve(db, ids, tokens=1)


def test_wrong_workspace_graph_is_rejected_before_reserving(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        with pytest.raises(ValueError, match="Workspace graph"):
            BudgetReservationService(db).reserve(workspace_id=uuid4(), graph_run_id=ids[3],
                                                 purpose="classification", plan=plan())
        assert db.scalars(select(ModelCallReservation)).all() == []


def test_concurrent_admission_only_reserves_available_budget(review_database):
    engine, ids = review_database
    start = Barrier(2)

    def attempt():
        with Session(engine) as db:
            start.wait(timeout=10)
            try:
                reserve(db, ids, tokens=3000)
                return "allowed"
            except BudgetReservationDenied as exc:
                return exc.reason

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(attempt) for _ in range(2)]
        assert sorted(future.result(timeout=15) for future in futures) == [
            "allowed", "token_budget_exceeded"]
    with Session(engine) as db:
        rows = db.scalars(select(ModelCallReservation)).all()
        assert sorted(row.status for row in rows) == ["denied", "reserved"]


def test_finalization_waits_for_admission_snapshot(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        reservation_id = reserve(db, ids).id
    connected = Event()
    pids = []

    def finalize():
        with Session(engine) as db:
            pids.append(db.scalar(text("select pg_backend_pid()")))
            connected.set()
            BudgetReservationService(db).finalize(workspace_id=ids[0],
                                                  reservation_id=reservation_id)

    with Session(engine) as reader, ThreadPoolExecutor(max_workers=1) as pool:
        reader.scalar(select(Workspace).where(Workspace.id == ids[0]).with_for_update())
        future = pool.submit(finalize)
        try:
            assert connected.wait(5)
            deadline = time.monotonic() + 4
            blocked = False
            while time.monotonic() < deadline:
                with engine.connect() as observer:
                    blocked = observer.scalar(text(
                        "select wait_event_type = 'Lock' from pg_stat_activity where pid = :pid"
                    ), {"pid": pids[0]})
                if blocked:
                    break
                time.sleep(0.02)
            assert blocked, "finalization bypassed the admission lock"
            assert reader.get(ModelCallReservation, reservation_id).status == "reserved"
        finally:
            reader.rollback()
        future.result(timeout=10)


def test_other_workspace_usage_and_ledger_links_are_isolated(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        first = reserve(db, ids, tokens=3000)
        MockModelProvider(db).complete(workspace_id=ids[0], graph_run_id=ids[3],
                                      purpose="classification", language=SupportedLanguage.en,
                                      prompt="Hello", completion_text="Answer")
        other = Workspace(name="Other", created_by_user_id=ids[2][0])
        db.add(other)
        db.flush()
        agent = AgentConfig(workspace_id=other.id, name="Other agent")
        db.add(agent)
        db.flush()
        run = GraphRun(workspace_id=other.id, agent_config_id=agent.id, user_id=ids[2][0],
                       input_message="Other", status=GraphRunStatus.running)
        db.add(run)
        db.commit()
        service = BudgetReservationService(db)
        second = service.reserve(workspace_id=other.id, graph_run_id=run.id,
                                 purpose="classification", plan=plan(tokens=3999))
        assert second.status == "reserved"
        ledger = MockModelProvider(db).complete(
            workspace_id=other.id, graph_run_id=run.id, purpose="classification",
            language=SupportedLanguage.en, prompt="Other", completion_text="Answer").ai_run
        with pytest.raises(ValueError, match="Reservation AI run was not found"):
            service.finalize(workspace_id=ids[0], reservation_id=first.id, ai_run_id=ledger.id)
        db.rollback()
        assert db.get(ModelCallReservation, first.id).ai_run_id is None
