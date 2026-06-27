from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.costs import CostPurposeSummaryResponse, CostSummaryResponse
from app.services.cost_service import CostService

router = APIRouter(prefix="/workspaces/{workspace_id}/costs", tags=["costs"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.get("/summary", response_model=CostSummaryResponse)
def get_cost_summary(workspace: WorkspaceMemberAccess, db: DbSession) -> CostSummaryResponse:
    summary = CostService(db).summarize_workspace(workspace_id=workspace.id)
    return CostSummaryResponse(
        workspace_id=summary.workspace_id,
        total_runs=summary.total_runs,
        total_tokens=summary.total_tokens,
        total_estimated_cost=summary.total_estimated_cost,
        average_latency_ms=summary.average_latency_ms,
        cache_hit_rate=summary.cache_hit_rate,
        by_purpose=[
            CostPurposeSummaryResponse(
                purpose=item.purpose,
                runs=item.runs,
                tokens=item.tokens,
                estimated_cost=item.estimated_cost,
            )
            for item in summary.by_purpose
        ],
    )
