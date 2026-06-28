from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import String, cast, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, GraphRun, GraphRunStatus, GraphStepStatus, ToolCall
from app.models.ai import AIRun, AIRunStatus
from app.services.budget_policy_service import BudgetPolicyService, BudgetUsage


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
class CostAgentSummary:
    agent_id: UUID
    agent_name: str
    graph_runs: int
    model_calls: int
    tokens: int
    estimated_cost: float
    average_latency_ms: float


@dataclass(frozen=True)
class CostRunSummary:
    graph_run_id: UUID
    agent_name: str
    status: str
    route_decision: str | None
    model_calls: int
    tokens: int
    estimated_cost: float
    latency_ms: int
    created_at: datetime


@dataclass(frozen=True)
class RecentAIRunSummary:
    id: UUID
    graph_run_id: UUID | None
    provider: str
    model: str
    model_config_id: UUID | None
    purpose: str
    language: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    latency_ms: int
    cache_hit: bool
    status: str
    error_message: str | None
    created_at: datetime


@dataclass(frozen=True)
class CostSummary:
    workspace_id: UUID
    budget_policy: object
    budget_usage: BudgetUsage
    total_runs: int
    total_tokens: int
    total_estimated_cost: float
    average_latency_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    cache_hit_rate: float
    failed_ai_runs: int
    failed_graph_runs: int
    failed_tool_calls: int
    graph_run_total: int
    ai_run_total: int
    by_purpose: list[CostPurposeSummary]
    by_model: list[CostModelSummary]
    by_agent: list[CostAgentSummary]
    recent_runs: list[CostRunSummary]
    recent_ai_runs: list[RecentAIRunSummary]


class CostService:
    def __init__(self, db: Session):
        self.db = db

    def summarize_workspace(
        self,
        *,
        workspace_id: UUID,
        search: str | None = None,
        graph_run_status: str = "all",
        ai_run_status: str = "all",
        graph_run_limit: int = 20,
        graph_run_offset: int = 0,
        ai_run_limit: int = 20,
        ai_run_offset: int = 0,
    ) -> CostSummary:
        total_runs = (
            self.db.scalar(select(func.count(AIRun.id)).where(AIRun.workspace_id == workspace_id))
            or 0
        )
        total_tokens = (
            self.db.scalar(
                select(func.coalesce(func.sum(AIRun.total_tokens), 0)).where(
                    AIRun.workspace_id == workspace_id
                )
            )
            or 0
        )
        total_cost = (
            self.db.scalar(
                select(func.coalesce(func.sum(AIRun.estimated_cost), 0.0)).where(
                    AIRun.workspace_id == workspace_id
                )
            )
            or 0.0
        )
        average_latency = (
            self.db.scalar(
                select(func.coalesce(func.avg(AIRun.latency_ms), 0.0)).where(
                    AIRun.workspace_id == workspace_id
                )
            )
            or 0.0
        )
        cache_hits = (
            self.db.scalar(
                select(func.count(AIRun.id)).where(
                    AIRun.workspace_id == workspace_id, AIRun.cache_hit
                )
            )
            or 0
        )
        failed_ai_runs = (
            self.db.scalar(
                select(func.count(AIRun.id)).where(
                    AIRun.workspace_id == workspace_id,
                    AIRun.status == AIRunStatus.failed,
                )
            )
            or 0
        )
        failed_graph_runs = (
            self.db.scalar(
                select(func.count(GraphRun.id)).where(
                    GraphRun.workspace_id == workspace_id,
                    GraphRun.status == GraphRunStatus.failed,
                )
            )
            or 0
        )
        failed_tool_calls = (
            self.db.scalar(
                select(func.count(ToolCall.id)).where(
                    ToolCall.workspace_id == workspace_id,
                    ToolCall.status == GraphStepStatus.failed,
                )
            )
            or 0
        )
        latency_values = list(
            self.db.scalars(
                select(AIRun.latency_ms)
                .where(AIRun.workspace_id == workspace_id)
                .order_by(AIRun.latency_ms.asc())
            ).all()
        )
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
        grouped_by_agent = self.db.execute(
            select(
                AgentConfig.id,
                AgentConfig.name,
                func.count(distinct(GraphRun.id)),
                func.count(AIRun.id),
                func.coalesce(func.sum(AIRun.total_tokens), 0),
                func.coalesce(func.sum(AIRun.estimated_cost), 0.0),
                func.coalesce(func.avg(AIRun.latency_ms), 0.0),
            )
            .join(GraphRun, GraphRun.id == AIRun.graph_run_id)
            .join(AgentConfig, AgentConfig.id == GraphRun.agent_config_id)
            .where(AIRun.workspace_id == workspace_id)
            .group_by(AgentConfig.id, AgentConfig.name)
            .order_by(func.coalesce(func.sum(AIRun.estimated_cost), 0.0).desc())
        ).all()
        graph_run_total = (
            self.db.scalar(
                select(func.count(distinct(GraphRun.id)))
                .select_from(AIRun)
                .join(GraphRun, GraphRun.id == AIRun.graph_run_id)
                .join(AgentConfig, AgentConfig.id == GraphRun.agent_config_id)
                .where(*_graph_run_cost_filters(workspace_id, search, graph_run_status))
            )
            or 0
        )
        ai_run_total = (
            self.db.scalar(
                select(func.count(AIRun.id))
                .select_from(AIRun)
                .outerjoin(GraphRun, AIRun.graph_run_id == GraphRun.id)
                .outerjoin(AgentConfig, GraphRun.agent_config_id == AgentConfig.id)
                .where(*_ai_run_cost_filters(workspace_id, search, ai_run_status))
            )
            or 0
        )
        grouped_by_run_statement = (
            select(
                GraphRun.id,
                AgentConfig.name,
                GraphRun.status,
                GraphRun.route_decision,
                func.count(AIRun.id),
                func.coalesce(func.sum(AIRun.total_tokens), 0),
                func.coalesce(func.sum(AIRun.estimated_cost), 0.0),
                func.coalesce(func.sum(AIRun.latency_ms), 0),
                GraphRun.created_at,
            )
            .join(GraphRun, GraphRun.id == AIRun.graph_run_id)
            .join(AgentConfig, AgentConfig.id == GraphRun.agent_config_id)
            .where(*_graph_run_cost_filters(workspace_id, search, graph_run_status))
            .group_by(
                GraphRun.id,
                AgentConfig.name,
                GraphRun.status,
                GraphRun.route_decision,
                GraphRun.created_at,
            )
            .order_by(GraphRun.created_at.desc())
            .offset(max(graph_run_offset, 0))
            .limit(_bounded_limit(graph_run_limit))
        )
        grouped_by_run = self.db.execute(grouped_by_run_statement).all()
        recent_ai_statement = (
            select(AIRun)
            .outerjoin(GraphRun, AIRun.graph_run_id == GraphRun.id)
            .outerjoin(AgentConfig, GraphRun.agent_config_id == AgentConfig.id)
            .where(*_ai_run_cost_filters(workspace_id, search, ai_run_status))
            .order_by(AIRun.created_at.desc())
            .offset(max(ai_run_offset, 0))
            .limit(_bounded_limit(ai_run_limit))
        )
        recent_ai_runs = list(self.db.scalars(recent_ai_statement).all())
        budget_service = BudgetPolicyService(self.db)
        policy = budget_service.get_or_create(workspace_id=workspace_id)
        usage = budget_service.current_month_usage(workspace_id=workspace_id)
        return CostSummary(
            workspace_id=workspace_id,
            budget_policy=policy,
            budget_usage=usage,
            total_runs=int(total_runs),
            total_tokens=int(total_tokens),
            total_estimated_cost=round(float(total_cost), 8),
            average_latency_ms=round(float(average_latency), 2),
            latency_p50_ms=_percentile(latency_values, 50),
            latency_p95_ms=_percentile(latency_values, 95),
            latency_p99_ms=_percentile(latency_values, 99),
            cache_hit_rate=round((int(cache_hits) / int(total_runs)) if total_runs else 0.0, 4),
            failed_ai_runs=int(failed_ai_runs),
            failed_graph_runs=int(failed_graph_runs),
            failed_tool_calls=int(failed_tool_calls),
            graph_run_total=int(graph_run_total),
            ai_run_total=int(ai_run_total),
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
            by_agent=[
                CostAgentSummary(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    graph_runs=int(graph_runs),
                    model_calls=int(model_calls),
                    tokens=int(tokens),
                    estimated_cost=round(float(cost), 8),
                    average_latency_ms=round(float(average_latency), 2),
                )
                for (
                    agent_id,
                    agent_name,
                    graph_runs,
                    model_calls,
                    tokens,
                    cost,
                    average_latency,
                ) in grouped_by_agent
            ],
            recent_runs=[
                CostRunSummary(
                    graph_run_id=graph_run_id,
                    agent_name=agent_name,
                    status=str(status),
                    route_decision=route_decision,
                    model_calls=int(model_calls),
                    tokens=int(tokens),
                    estimated_cost=round(float(cost), 8),
                    latency_ms=int(latency_ms),
                    created_at=created_at,
                )
                for (
                    graph_run_id,
                    agent_name,
                    status,
                    route_decision,
                    model_calls,
                    tokens,
                    cost,
                    latency_ms,
                    created_at,
                ) in grouped_by_run
            ],
            recent_ai_runs=[
                RecentAIRunSummary(
                    id=run.id,
                    graph_run_id=run.graph_run_id,
                    provider=run.provider,
                    model=run.model,
                    model_config_id=run.model_config_id,
                    purpose=run.purpose,
                    language=str(run.language),
                    prompt_tokens=run.prompt_tokens,
                    completion_tokens=run.completion_tokens,
                    total_tokens=run.total_tokens,
                    estimated_cost=round(float(run.estimated_cost), 8),
                    latency_ms=run.latency_ms,
                    cache_hit=run.cache_hit,
                    status=str(run.status),
                    error_message=run.error_message,
                    created_at=run.created_at,
                )
                for run in recent_ai_runs
            ],
        )


def _percentile(values: list[int], percentile: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    rank = round((percentile / 100) * (len(values) - 1))
    return float(values[min(max(rank, 0), len(values) - 1)])


def _bounded_limit(limit: int) -> int:
    return max(min(limit, 100), 1)


def _graph_run_cost_filters(workspace_id: UUID, search: str | None, status_filter: str):
    filters = [AIRun.workspace_id == workspace_id]
    if status_filter != "all":
        filters.append(
            or_(
                cast(GraphRun.status, String) == status_filter,
                GraphRun.route_decision == status_filter,
            )
        )
    search_term = (search or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        filters.append(
            or_(
                cast(GraphRun.id, String).ilike(pattern),
                AgentConfig.name.ilike(pattern),
                cast(GraphRun.status, String).ilike(pattern),
                GraphRun.route_decision.ilike(pattern),
            )
        )
    return filters


def _ai_run_cost_filters(workspace_id: UUID, search: str | None, status_filter: str):
    filters = [AIRun.workspace_id == workspace_id]
    if status_filter != "all":
        filters.append(cast(AIRun.status, String) == status_filter)
    search_term = (search or "").strip()
    if search_term:
        pattern = f"%{search_term}%"
        filters.append(
            or_(
                cast(AIRun.id, String).ilike(pattern),
                cast(AIRun.graph_run_id, String).ilike(pattern),
                AIRun.provider.ilike(pattern),
                AIRun.model.ilike(pattern),
                AgentConfig.name.ilike(pattern),
                AIRun.purpose.ilike(pattern),
                cast(AIRun.language, String).ilike(pattern),
                cast(AIRun.status, String).ilike(pattern),
                AIRun.error_message.ilike(pattern),
            )
        )
    return filters
