import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.reservation import ModelCallReservation
from app.models.workspace import Workspace
from app.services.budgeted_model_provider import BudgetedModelProvider, ModelBudgetDenied
from app.services.model_provider import MockModelProvider


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_inflight_call_reserves_allowance_without_holding_lock(review_database, monkeypatch):
    engine, ids = review_database
    dispatched, release = Event(), Event()
    original = MockModelProvider.complete
    calls = []

    def paused(provider, **kwargs):
        calls.append(kwargs["purpose"])
        dispatched.set()
        assert release.wait(10), "mock dispatch wait expired"
        return original(provider, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", paused)
    args = dict(workspace_id=ids[0], graph_run_id=ids[3], language=SupportedLanguage.en,
                prompt="word " * 3000, completion_text="Answer", purpose="draft_response")

    def first_call():
        with Session(engine) as db:
            return BudgetedModelProvider(db).complete(**args).content

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(first_call)
        try:
            assert dispatched.wait(10)
            with Session(engine) as observer:
                # No admission lock spans provider I/O.
                observer.scalar(select(Workspace).where(Workspace.id == ids[0])
                                .with_for_update(nowait=True))
                observer.rollback()
            with Session(engine) as second:
                with pytest.raises(ModelBudgetDenied, match="token_budget_exceeded"):
                    BudgetedModelProvider(second).complete(**args)
        finally:
            release.set()
        assert first.result(timeout=10) == "Answer"
    assert calls == ["draft_response"]
    with Session(engine) as db:
        rows = db.scalars(select(ModelCallReservation)).all()
        assert sorted(row.status for row in rows) == ["consumed", "denied"]
