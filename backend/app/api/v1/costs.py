from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_permission
from app.models.workspace import Workspace
from app.schemas.costs import (
    BudgetPolicySummaryResponse,
    CostAgentSummaryResponse,
    CostModelSummaryResponse,
    CostPurposeSummaryResponse,
    CostRunSummaryResponse,
    CostSummaryResponse,
    RecentAIRunSummaryResponse,
)
from app.services.cost_service import CostService

router = APIRouter(prefix="/workspaces/{workspace_id}/costs", tags=["costs"])
DbSession = Annotated[Session, Depends(get_db)]
CostReadAccess = Annotated[Workspace, Depends(require_workspace_permission("costs:read"))]
CostSearch = Annotated[str | None, Query(max_length=240)]
GraphRunStatusFilter = Annotated[
    Literal["all", "completed", "needs_human_review", "failed", "human_review"], Query()
]
AIRunStatusFilter = Annotated[Literal["all", "succeeded", "failed"], Query()]
ListLimit = Annotated[int, Query(ge=1, le=100)]
ListOffset = Annotated[int, Query(ge=0)]


@router.get("/summary", response_model=CostSummaryResponse)
def get_cost_summary(
    workspace: CostReadAccess,
    db: DbSession,
    search: CostSearch = None,
    graph_run_status: GraphRunStatusFilter = "all",
    ai_run_status: AIRunStatusFilter = "all",
    graph_run_limit: ListLimit = 20,
    graph_run_offset: ListOffset = 0,
    ai_run_limit: ListLimit = 20,
    ai_run_offset: ListOffset = 0,
) -> CostSummaryResponse:
    summary = CostService(db).summarize_workspace(
        workspace_id=workspace.id,
        search=search,
        graph_run_status=graph_run_status,
        ai_run_status=ai_run_status,
        graph_run_limit=graph_run_limit,
        graph_run_offset=graph_run_offset,
        ai_run_limit=ai_run_limit,
        ai_run_offset=ai_run_offset,
    )
    return CostSummaryResponse(
        workspace_id=summary.workspace_id,
        budget_policy=BudgetPolicySummaryResponse(
            monthly_token_budget=summary.budget_policy.monthly_token_budget,
            monthly_cost_budget=summary.budget_policy.monthly_cost_budget,
            per_run_token_budget=summary.budget_policy.per_run_token_budget,
            per_run_cost_budget=summary.budget_policy.per_run_cost_budget,
            rate_limit_requests_per_hour=summary.budget_policy.rate_limit_requests_per_hour,
            alert_threshold_percent=summary.budget_policy.alert_threshold_percent,
            tokens_used_this_month=summary.budget_usage.tokens,
            estimated_cost_this_month=summary.budget_usage.estimated_cost,
            token_budget_used_percent=summary.budget_usage.token_budget_used_percent,
            cost_budget_used_percent=summary.budget_usage.cost_budget_used_percent,
            alerting=summary.budget_usage.alerting,
        ),
        total_runs=summary.total_runs,
        total_tokens=summary.total_tokens,
        total_estimated_cost=summary.total_estimated_cost,
        average_latency_ms=summary.average_latency_ms,
        latency_p50_ms=summary.latency_p50_ms,
        latency_p95_ms=summary.latency_p95_ms,
        latency_p99_ms=summary.latency_p99_ms,
        cache_hit_rate=summary.cache_hit_rate,
        failed_ai_runs=summary.failed_ai_runs,
        failed_graph_runs=summary.failed_graph_runs,
        failed_tool_calls=summary.failed_tool_calls,
        by_purpose=[
            CostPurposeSummaryResponse(
                purpose=item.purpose,
                runs=item.runs,
                tokens=item.tokens,
                estimated_cost=item.estimated_cost,
            )
            for item in summary.by_purpose
        ],
        by_model=[
            CostModelSummaryResponse(
                provider=item.provider,
                model=item.model,
                runs=item.runs,
                tokens=item.tokens,
                estimated_cost=item.estimated_cost,
            )
            for item in summary.by_model
        ],
        by_agent=[
            CostAgentSummaryResponse(
                agent_id=item.agent_id,
                agent_name=item.agent_name,
                graph_runs=item.graph_runs,
                model_calls=item.model_calls,
                tokens=item.tokens,
                estimated_cost=item.estimated_cost,
                average_latency_ms=item.average_latency_ms,
            )
            for item in summary.by_agent
        ],
        recent_runs=[
            CostRunSummaryResponse(
                graph_run_id=item.graph_run_id,
                agent_name=item.agent_name,
                status=item.status,
                route_decision=item.route_decision,
                model_calls=item.model_calls,
                tokens=item.tokens,
                estimated_cost=item.estimated_cost,
                latency_ms=item.latency_ms,
                created_at=item.created_at,
            )
            for item in summary.recent_runs
        ],
        recent_ai_runs=[
            RecentAIRunSummaryResponse(
                id=item.id,
                graph_run_id=item.graph_run_id,
                provider=item.provider,
                model=item.model,
                model_config_id=item.model_config_id,
                purpose=item.purpose,
                language=item.language,
                prompt_tokens=item.prompt_tokens,
                completion_tokens=item.completion_tokens,
                total_tokens=item.total_tokens,
                estimated_cost=item.estimated_cost,
                latency_ms=item.latency_ms,
                cache_hit=item.cache_hit,
                status=item.status,
                error_message=item.error_message,
                created_at=item.created_at,
            )
            for item in summary.recent_ai_runs
        ],
    )
