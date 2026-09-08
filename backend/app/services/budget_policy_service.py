from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun
from app.models.ai import AIRun
from app.models.budget import WorkspaceBudgetPolicy
from app.models.workspace import Workspace


@dataclass(frozen=True)
class BudgetUsage:
    tokens: int
    estimated_cost: float
    token_budget_used_percent: float
    cost_budget_used_percent: float
    alerting: bool


class BudgetPolicyService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, *, workspace_id: UUID) -> WorkspaceBudgetPolicy:
        policy = self.db.scalar(
            select(WorkspaceBudgetPolicy).where(WorkspaceBudgetPolicy.workspace_id == workspace_id)
        )
        if policy is not None:
            return policy
        # Costs, policy reads and admission can all initialize this row. Share admission's
        # workspace lock, then re-read after a competing initializer has committed.
        self.db.scalar(select(Workspace.id).where(Workspace.id == workspace_id)
                       .with_for_update(key_share=True))
        policy = self.db.scalar(
            select(WorkspaceBudgetPolicy).where(WorkspaceBudgetPolicy.workspace_id == workspace_id)
        )
        if policy is None:
            policy = WorkspaceBudgetPolicy(workspace_id=workspace_id)
            self.db.add(policy)
        # Release this initialization lock even when another caller created the policy.
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def update(
        self,
        *,
        workspace_id: UUID,
        monthly_token_budget: int,
        monthly_cost_budget: float,
        per_run_token_budget: int,
        per_run_cost_budget: float,
        rate_limit_requests_per_hour: int,
        alert_threshold_percent: float,
    ) -> WorkspaceBudgetPolicy:
        policy = self.get_or_create(workspace_id=workspace_id)
        policy.monthly_token_budget = monthly_token_budget
        policy.monthly_cost_budget = monthly_cost_budget
        policy.per_run_token_budget = per_run_token_budget
        policy.per_run_cost_budget = per_run_cost_budget
        policy.rate_limit_requests_per_hour = rate_limit_requests_per_hour
        policy.alert_threshold_percent = alert_threshold_percent
        policy.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def current_month_usage(self, *, workspace_id: UUID) -> BudgetUsage:
        policy = self.get_or_create(workspace_id=workspace_id)
        start = _month_start()
        tokens = self.db.scalar(
            select(func.coalesce(func.sum(AIRun.total_tokens), 0)).where(
                AIRun.workspace_id == workspace_id, AIRun.created_at >= start
            )
        ) or 0
        cost = self.db.scalar(
            select(func.coalesce(func.sum(AIRun.estimated_cost), 0.0)).where(
                AIRun.workspace_id == workspace_id, AIRun.created_at >= start
            )
        ) or 0.0
        token_percent = float(tokens) / float(policy.monthly_token_budget)
        cost_percent = float(cost) / float(policy.monthly_cost_budget)
        return BudgetUsage(
            tokens=int(tokens),
            estimated_cost=round(float(cost), 8),
            token_budget_used_percent=round(token_percent, 4),
            cost_budget_used_percent=round(cost_percent, 4),
            alerting=token_percent >= policy.alert_threshold_percent
            or cost_percent >= policy.alert_threshold_percent,
        )

    def effective_run_token_budget(self, *, workspace_id: UUID, agent_token_budget: int) -> int:
        policy = self.get_or_create(workspace_id=workspace_id)
        return min(agent_token_budget, policy.per_run_token_budget)

    def request_count_last_hour(self, *, workspace_id: UUID) -> int:
        since = datetime.now(UTC) - timedelta(hours=1)
        return int(
            self.db.scalar(
                select(func.count(GraphRun.id)).where(
                    GraphRun.workspace_id == workspace_id, GraphRun.created_at >= since
                )
            )
            or 0
        )

    def rate_limit_exceeded(self, *, workspace_id: UUID) -> bool:
        policy = self.get_or_create(workspace_id=workspace_id)
        request_count = self.request_count_last_hour(workspace_id=workspace_id)
        return request_count >= policy.rate_limit_requests_per_hour


def _month_start() -> datetime:
    now = datetime.now(UTC)
    return datetime(year=now.year, month=now.month, day=1, tzinfo=UTC)
