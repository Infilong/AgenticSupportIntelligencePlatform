import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.budget import WorkspaceBudgetPolicy
from app.models.evaluation import EvaluationRun, EvaluationRunStatus
from app.models.reservation import ModelCallReservation
from app.models.workspace import Workspace
from app.services.budgeted_model_provider import BudgetedModelProvider, ModelBudgetDenied
from app.services.model_provider import MockModelProvider

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL")


@pytest.mark.parametrize("competing_context", ["graph", "evaluation"])
def test_baseline_reserves_shared_allowance_before_dispatch(
    review_database, monkeypatch, competing_context,
):
    engine, ids = review_database
    with Session(engine) as db:
        evaluation = EvaluationRun(workspace_id=ids[0], name="Budget concurrency",
            modes_json='["direct_llm"]', status=EvaluationRunStatus.running,
            total_cases=2, created_by_user_id=ids[2][0])
        db.add(evaluation)
        db.add(WorkspaceBudgetPolicy(workspace_id=ids[0], monthly_token_budget=4000))
        db.commit()
        evaluation_id = evaluation.id
    dispatched, release = Event(), Event()
    original = MockModelProvider.complete
    calls = []

    def paused(self, **kwargs):
        calls.append(kwargs["purpose"])
        dispatched.set()
        assert release.wait(10), "dispatch observation deadline exceeded"
        return original(self, **kwargs)

    monkeypatch.setattr(MockModelProvider, "complete", paused)
    args = dict(workspace_id=ids[0], evaluation_run_id=evaluation_id,
                purpose="evaluation_direct_llm", language=SupportedLanguage.en,
                prompt="word " * 3000, completion_text="Answer")

    def first_call():
        with Session(engine) as db:
            return BudgetedModelProvider(db).complete(**args).content

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(first_call)
        try:
            assert dispatched.wait(10)
            with Session(engine) as observer:
                observer.scalar(select(Workspace).where(Workspace.id == ids[0])
                                .with_for_update(nowait=True))
                observer.rollback()
            competing = dict(args)
            reason = "token_budget_exceeded"
            if competing_context == "graph":
                competing.pop("evaluation_run_id")
                competing.update(graph_run_id=ids[3], purpose="draft_response")
                reason = "monthly_token_budget_exceeded"
            with Session(engine) as db, pytest.raises(ModelBudgetDenied, match=reason):
                BudgetedModelProvider(db).complete(**competing)
        finally:
            release.set()
        assert first.result(timeout=10) == "Answer"
    assert calls == ["evaluation_direct_llm"]
    with Session(engine) as db:
        reservations = db.scalars(select(ModelCallReservation)).all()
        assert sorted(row.status for row in reservations) == ["consumed", "denied"]
        first = next(row for row in reservations if row.status == "consumed")
        assert first.evaluation_run_id == evaluation_id and first.graph_run_id is None
        assert first.ai_run_id is not None
