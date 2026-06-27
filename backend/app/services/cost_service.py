from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai import AIRun


@dataclass(frozen=True)
class CostPurposeSummary:
    purpose: str
    runs: int
    tokens: int
    estimated_cost: float


@dataclass(frozen=True)
class CostModelSummary:
    provider: str
    model: str
    runs: int
    tokens: int
    estimated_cost: float


@dataclass(frozen=True)
class CostSummary:
    workspace_id: UUID
    total_runs: int
    total_tokens: int
    total_estimated_cost: float
    average_latency_ms: float
    cache_hit_rate: float
    by_purpose: list[CostPurposeSummary]
    by_model: list[CostModelSummary]


class CostService:
    def __init__(self, db: Session):
        self.db = db

    def summarize_workspace(self, *, workspace_id: UUID) -> CostSummary:
        total_runs = self.db.scalar(
            select(func.count(AIRun.id)).where(AIRun.workspace_id == workspace_id)
        ) or 0
        total_tokens = self.db.scalar(
            select(func.coalesce(func.sum(AIRun.total_tokens), 0)).where(
                AIRun.workspace_id == workspace_id
            )
        ) or 0
        total_cost = self.db.scalar(
            select(func.coalesce(func.sum(AIRun.estimated_cost), 0.0)).where(
                AIRun.workspace_id == workspace_id
            )
        ) or 0.0
        average_latency = self.db.scalar(
            select(func.coalesce(func.avg(AIRun.latency_ms), 0.0)).where(
                AIRun.workspace_id == workspace_id
            )
        ) or 0.0
        cache_hits = self.db.scalar(
            select(func.count(AIRun.id)).where(AIRun.workspace_id == workspace_id, AIRun.cache_hit)
        ) or 0
        grouped = self.db.execute(
            select(
                AIRun.purpose,
                func.count(AIRun.id),
                func.coalesce(func.sum(AIRun.total_tokens), 0),
                func.coalesce(func.sum(AIRun.estimated_cost), 0.0),
            )
            .where(AIRun.workspace_id == workspace_id)
            .group_by(AIRun.purpose)
            .order_by(AIRun.purpose.asc())
        ).all()
        grouped_by_model = self.db.execute(
            select(
                AIRun.provider,
                AIRun.model,
                func.count(AIRun.id),
                func.coalesce(func.sum(AIRun.total_tokens), 0),
                func.coalesce(func.sum(AIRun.estimated_cost), 0.0),
            )
            .where(AIRun.workspace_id == workspace_id)
            .group_by(AIRun.provider, AIRun.model)
            .order_by(AIRun.provider.asc(), AIRun.model.asc())
        ).all()
        return CostSummary(
            workspace_id=workspace_id,
            total_runs=int(total_runs),
            total_tokens=int(total_tokens),
            total_estimated_cost=round(float(total_cost), 8),
            average_latency_ms=round(float(average_latency), 2),
            cache_hit_rate=round((int(cache_hits) / int(total_runs)) if total_runs else 0.0, 4),
            by_purpose=[
                CostPurposeSummary(
                    purpose=purpose,
                    runs=int(runs),
                    tokens=int(tokens),
                    estimated_cost=round(float(cost), 8),
                )
                for purpose, runs, tokens, cost in grouped
            ],
            by_model=[
                CostModelSummary(
                    provider=provider,
                    model=model,
                    runs=int(runs),
                    tokens=int(tokens),
                    estimated_cost=round(float(cost), 8),
                )
                for provider, model, runs, tokens, cost in grouped_by_model
            ],
        )
