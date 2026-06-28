from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.evaluation import (
    EvaluationDetailResponse,
    EvaluationMetricResponse,
    EvaluationResultResponse,
    EvaluationRunFolderUpdateRequest,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.agent_service import AgentNotFoundError
from app.services.audit_log_service import AuditLogService
from app.services.evaluation_loader import EvaluationCaseLoadError
from app.services.evaluation_runner import EvaluationRunner, EvaluationRunNotFoundError
from app.services.folder_service import ResourceFolderNotFoundError

router = APIRouter(prefix="/workspaces/{workspace_id}/evaluations", tags=["evaluations"])
DbSession = Annotated[Session, Depends(get_db)]
EvaluationReadAccess = Annotated[
    Workspace, Depends(require_workspace_permission("evaluations:read"))
]
EvaluationRunAccess = Annotated[Workspace, Depends(require_workspace_permission("evaluations:run"))]
ResourceDeleteAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resources:delete"))
]
ResourceFolderManageAccess = Annotated[
    Workspace, Depends(require_workspace_permission("resource_folders:manage"))
]
CurrentUser = Annotated[User, Depends(get_current_user)]
EvaluationId = Annotated[UUID, Path()]
IncludeArchived = Annotated[bool, Query()]
FolderFilter = Annotated[UUID | None, Query()]


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
            folder_id=payload.folder_id,
        )
        detail = EvaluationRunner(db).get_run_detail(workspace_id=workspace.id, run_id=run.id)
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "agent_not_found", "message": "Agent was not found."},
        ) from exc
    except EvaluationCaseLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "evaluation_case_load_failed", "message": str(exc)},
        ) from exc
    return _detail_response(detail)


@router.get("", response_model=list[EvaluationRunResponse])
def list_evaluations(
    workspace: EvaluationReadAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
    folder_id: FolderFilter = None,
) -> list[EvaluationRunResponse]:
    try:
        runs = EvaluationRunner(db).list_runs(
            workspace_id=workspace.id, include_archived=include_archived, folder_id=folder_id
        )
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return [EvaluationRunResponse.model_validate(run) for run in runs]


@router.get("/{evaluation_id}", response_model=EvaluationDetailResponse)
def get_evaluation(
    evaluation_id: EvaluationId,
    workspace: EvaluationReadAccess,
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


@router.patch("/{evaluation_id}/folder", response_model=EvaluationRunResponse)
def move_evaluation_folder(
    evaluation_id: EvaluationId,
    payload: EvaluationRunFolderUpdateRequest,
    workspace: ResourceFolderManageAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> EvaluationRunResponse:
    try:
        run = EvaluationRunner(db).move_run(
            workspace_id=workspace.id, run_id=evaluation_id, folder_id=payload.folder_id
        )
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "evaluation_not_found", "message": "Evaluation was not found."},
        ) from exc
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="evaluation.moved",
        resource_type="evaluation_run",
        resource_id=run.id,
        metadata={"folder_id": str(run.folder_id) if run.folder_id else None},
    )
    return EvaluationRunResponse.model_validate(run)


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


def _folder_not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "resource_folder_not_found", "message": "Resource folder was not found."},
    )


def _detail_response(run) -> EvaluationDetailResponse:
    return EvaluationDetailResponse(
        run=EvaluationRunResponse.model_validate(run),
        results=[EvaluationResultResponse.model_validate(result) for result in run.results],
        metrics=[EvaluationMetricResponse.model_validate(metric) for metric in run.metrics],
    )
