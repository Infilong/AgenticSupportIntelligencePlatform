from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.guardrail import (
    GuardrailCatalogItemResponse,
    GuardrailFailureResponse,
    GuardrailUsageSummaryResponse,
)
from app.services.guardrail_catalog_service import GuardrailCatalogItem, GuardrailCatalogService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["guardrails"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.get("/guardrails", response_model=list[GuardrailCatalogItemResponse])
def list_guardrails(
    workspace: WorkspaceMemberAccess, db: DbSession
) -> list[GuardrailCatalogItemResponse]:
    guardrails = GuardrailCatalogService(db).list_guardrails(workspace_id=workspace.id)
    return [_guardrail_response(guardrail) for guardrail in guardrails]


def _guardrail_response(guardrail: GuardrailCatalogItem) -> GuardrailCatalogItemResponse:
    definition = guardrail.definition
    return GuardrailCatalogItemResponse(
        guardrail_type=definition.guardrail_type,
        label=definition.label,
        description=definition.description,
        stage=definition.stage,
        enabled=definition.enabled,
        configurable=definition.configurable,
        default_severity=definition.default_severity,
        action_on_fail=definition.action_on_fail,
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
