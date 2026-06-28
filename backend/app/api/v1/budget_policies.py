from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.budget_policy import BudgetPolicyResponse, BudgetPolicyUpdateRequest
from app.services.audit_log_service import AuditLogService
from app.services.budget_policy_service import BudgetPolicyService

router = APIRouter(prefix="/workspaces/{workspace_id}/budget-policy", tags=["budget-policy"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
BudgetReadAccess = Annotated[Workspace, Depends(require_workspace_permission("budget_policy:read"))]
BudgetManageAccess = Annotated[
    Workspace, Depends(require_workspace_permission("budget_policy:manage"))
]


@router.get("", response_model=BudgetPolicyResponse)
def get_budget_policy(workspace: BudgetReadAccess, db: DbSession) -> BudgetPolicyResponse:
    policy = BudgetPolicyService(db).get_or_create(workspace_id=workspace.id)
    return BudgetPolicyResponse.model_validate(policy)


@router.put("", response_model=BudgetPolicyResponse)
def update_budget_policy(
    payload: BudgetPolicyUpdateRequest,
    workspace: BudgetManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> BudgetPolicyResponse:
    policy = BudgetPolicyService(db).update(
        workspace_id=workspace.id,
        monthly_token_budget=payload.monthly_token_budget,
        monthly_cost_budget=payload.monthly_cost_budget,
        per_run_token_budget=payload.per_run_token_budget,
        per_run_cost_budget=payload.per_run_cost_budget,
        rate_limit_requests_per_hour=payload.rate_limit_requests_per_hour,
        alert_threshold_percent=payload.alert_threshold_percent,
    )
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="budget_policy.updated",
        resource_type="budget_policy",
        resource_id=policy.id,
        metadata={
            "monthly_token_budget": policy.monthly_token_budget,
            "monthly_cost_budget": policy.monthly_cost_budget,
            "per_run_token_budget": policy.per_run_token_budget,
            "per_run_cost_budget": policy.per_run_cost_budget,
            "rate_limit_requests_per_hour": policy.rate_limit_requests_per_hour,
            "alert_threshold_percent": policy.alert_threshold_percent,
        },
    )
    return BudgetPolicyResponse.model_validate(policy)
