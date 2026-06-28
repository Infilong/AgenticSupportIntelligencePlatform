from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.guardrail import (
    GuardrailCatalogItemResponse,
    GuardrailFailureResponse,
    GuardrailPolicyUpdateRequest,
    GuardrailUsageSummaryResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.guardrail_catalog_service import (
    GuardrailCatalogItem,
    GuardrailCatalogService,
    GuardrailPolicyNotConfigurableError,
    GuardrailPolicyNotFoundError,
)

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["guardrails"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
GuardrailReadAccess = Annotated[Workspace, Depends(require_workspace_permission("guardrails:read"))]
GuardrailConfigureAccess = Annotated[
    Workspace, Depends(require_workspace_permission("guardrails:configure"))
]
GuardrailType = Annotated[str, Path(min_length=1, max_length=120)]


@router.get("/guardrails", response_model=list[GuardrailCatalogItemResponse])
def list_guardrails(
    workspace: GuardrailReadAccess, db: DbSession
) -> list[GuardrailCatalogItemResponse]:
    guardrails = GuardrailCatalogService(db).list_guardrails(workspace_id=workspace.id)
    return [_guardrail_response(guardrail) for guardrail in guardrails]


@router.patch("/guardrails/{guardrail_type}/policy", response_model=GuardrailCatalogItemResponse)
def update_guardrail_policy(
    guardrail_type: GuardrailType,
    payload: GuardrailPolicyUpdateRequest,
    workspace: GuardrailConfigureAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> GuardrailCatalogItemResponse:
    try:
        guardrail = GuardrailCatalogService(db).update_policy(
            workspace_id=workspace.id,
            guardrail_type=guardrail_type,
            enabled=payload.enabled,
            severity=payload.severity,
            action_on_fail=payload.action_on_fail,
            threshold=payload.threshold,
        )
    except GuardrailPolicyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "guardrail_policy_not_found", "message": str(exc)},
        ) from exc
    except GuardrailPolicyNotConfigurableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "guardrail_policy_not_configurable", "message": str(exc)},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="guardrail_policy.updated",
        resource_type="guardrail_policy",
        metadata={
            "guardrail_type": guardrail_type,
            "enabled": payload.enabled,
            "severity": payload.severity,
            "action_on_fail": payload.action_on_fail,
            "threshold": payload.threshold,
        },
    )
    return _guardrail_response(guardrail)


def _guardrail_response(guardrail: GuardrailCatalogItem) -> GuardrailCatalogItemResponse:
    definition = guardrail.definition
    return GuardrailCatalogItemResponse(
        guardrail_type=definition.guardrail_type,
        label=definition.label,
        description=definition.description,
        stage=definition.stage,
        enabled=guardrail.policy.enabled,
        configurable=definition.configurable,
        default_severity=definition.default_severity,
        severity=guardrail.policy.severity,
        action_on_fail=guardrail.policy.action_on_fail,
        threshold=guardrail.policy.threshold,
        related_workflow_nodes=definition.related_workflow_nodes,
        usage=GuardrailUsageSummaryResponse(
            total_evaluations=guardrail.usage.total_evaluations,
            failed_evaluations=guardrail.usage.failed_evaluations,
            pass_rate=guardrail.usage.pass_rate,
            last_failed_at=guardrail.usage.last_failed_at,
        ),
        recent_failures=[
            GuardrailFailureResponse(
                id=failure.id,
                graph_run_id=failure.graph_run_id,
                graph_step_id=failure.graph_step_id,
                severity=failure.severity,
                message=failure.message,
                created_at=failure.created_at,
            )
            for failure in guardrail.recent_failures
        ],
    )
