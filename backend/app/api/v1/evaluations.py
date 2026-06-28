from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.evaluation import (
    EvaluationDetailResponse,
    EvaluationMetricResponse,
    EvaluationResultResponse,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.evaluation_loader import EvaluationCaseLoadError
from app.services.evaluation_runner import EvaluationRunner, EvaluationRunNotFoundError

router = APIRouter(prefix="/workspaces/{workspace_id}/evaluations", tags=["evaluations"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
EvaluationRunAccess = Annotated[
    Workspace, Depends(require_workspace_permission("evaluations:run"))
]
ResourceDeleteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resources:delete"))
]
CurrentUser = Annotated[User, Depends(get_current_user)]
EvaluationId = Annotated[UUID, Path()]
IncludeArchived = Annotated[bool, Query()]


@router.post("", response_model=EvaluationDetailResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation(
    payload: EvaluationRunRequest,
    workspace: EvaluationRunAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> EvaluationDetailResponse:
    try:
        run = EvaluationRunner(db).run_from_jsonl(
            workspace_id=workspace.id,
            name=payload.name,
            jsonl_cases=payload.jsonl_cases,
            modes=payload.modes,
            current_user=current_user,
            agent_id=payload.agent_id,
        )
        detail = EvaluationRunner(db).get_run_detail(workspace_id=workspace.id, run_id=run.id)
    except EvaluationCaseLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "evaluation_case_load_failed", "message": str(exc)},
        ) from exc
    return _detail_response(detail)


@router.get("", response_model=list[EvaluationRunResponse])
def list_evaluations(
    workspace: WorkspaceMemberAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
) -> list[EvaluationRunResponse]:
    runs = EvaluationRunner(db).list_runs(
        workspace_id=workspace.id, include_archived=include_archived
    )
    return [EvaluationRunResponse.model_validate(run) for run in runs]


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
def get_evaluation(
    evaluation_id: EvaluationId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> EvaluationDetailResponse:
    try:
        detail = EvaluationRunner(db).get_run_detail(
            workspace_id=workspace.id, run_id=evaluation_id
        )
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "evaluation_not_found", "message": "Evaluation was not found."},
        ) from exc
    return _detail_response(detail)


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_evaluation(
    evaluation_id: EvaluationId,
    workspace: ResourceDeleteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        run = EvaluationRunner(db).archive_run(workspace_id=workspace.id, run_id=evaluation_id)
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "evaluation_not_found", "message": "Evaluation was not found."},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="evaluation.archived",
        resource_type="evaluation_run",
        resource_id=run.id,
        metadata={
            "name": run.name,
            "archived_at": run.archived_at.isoformat() if run.archived_at else None,
        },
    )


def _detail_response(run) -> EvaluationDetailResponse:
    return EvaluationDetailResponse(
        run=EvaluationRunResponse.model_validate(run),
        results=[EvaluationResultResponse.model_validate(result) for result in run.results],
        metrics=[EvaluationMetricResponse.model_validate(metric) for metric in run.metrics],
    )
