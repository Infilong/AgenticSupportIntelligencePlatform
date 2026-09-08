from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.ai import AIRun
from app.models.evaluation import EvaluationRunStatus
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.evaluation import (
    EvaluationComparisonResponse,
    EvaluationDetailResponse,
    EvaluationMetricResponse,
    EvaluationPromptVersionResponse,
    EvaluationResultResponse,
    EvaluationRunFolderUpdateRequest,
    EvaluationRunRequest,
    EvaluationRunResponse,
)
from app.services.agent_service import AgentNotFoundError
from app.services.budget_reservations import EvaluationReservationActive
from app.services.evaluation_loader import EvaluationCaseLoadError
from app.services.evaluation_management import EvaluationRunActiveError
from app.services.evaluation_runner import (
    EvaluationRunner,
    EvaluationRunNotArchivedError,
    EvaluationRunNotFoundError,
)
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
SearchFilter = Annotated[str | None, Query(max_length=120)]
ListLimit = Annotated[int | None, Query(ge=1, le=500)]
ListOffset = Annotated[int, Query(ge=0)]
UnfiledFilter = Annotated[bool, Query()]
ArchivedOnlyFilter = Annotated[bool, Query()]
StatusFilter = Annotated[EvaluationRunStatus | None, Query(alias="status")]


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
    return _detail_response(detail, db=db)


@router.get("", response_model=list[EvaluationRunResponse])
def list_evaluations(
    workspace: EvaluationReadAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
    archived_only: ArchivedOnlyFilter = False,
    folder_id: FolderFilter = None,
    unfiled: UnfiledFilter = False,
    search: SearchFilter = None,
    status_filter: StatusFilter = None,
    limit: ListLimit = None,
    offset: ListOffset = 0,
) -> list[EvaluationRunResponse]:
    if folder_id is not None and unfiled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "evaluation_filter_conflict",
                "message": "Use either folder_id or unfiled, not both.",
            },
        )
    try:
        runs = EvaluationRunner(db).list_runs(
            workspace_id=workspace.id,
            include_archived=include_archived,
            archived_only=archived_only,
            folder_id=folder_id,
            unfiled=unfiled,
            search=search,
            status_filter=status_filter,
            limit=limit,
            offset=offset,
        )
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return [EvaluationRunResponse.model_validate(run) for run in runs]


@router.get("/{evaluation_id}/compare/{baseline_id}", response_model=EvaluationComparisonResponse)
def compare_evaluations(
    evaluation_id: EvaluationId,
    baseline_id: UUID,
    workspace: EvaluationReadAccess,
    db: DbSession,
) -> EvaluationComparisonResponse:
    try:
        current_run, baseline_run, deltas = EvaluationRunner(db).compare_runs(
            workspace_id=workspace.id,
            current_run_id=evaluation_id,
            baseline_run_id=baseline_id,
        )
    except EvaluationRunNotFoundError as exc:
        raise _evaluation_not_found() from exc
    return EvaluationComparisonResponse(
        current_run=EvaluationRunResponse.model_validate(current_run),
        baseline_run=EvaluationRunResponse.model_validate(baseline_run),
        deltas=deltas,
        improvement_count=sum(1 for delta in deltas if delta["direction"] == "improved"),
        regression_count=sum(1 for delta in deltas if delta["direction"] == "regressed"),
        new_metric_count=sum(1 for delta in deltas if delta["direction"] == "new"),
        missing_metric_count=sum(1 for delta in deltas if delta["direction"] == "missing"),
    )


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
        raise _evaluation_not_found() from exc
    return _detail_response(detail, db=db)


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
            workspace_id=workspace.id, run_id=evaluation_id, folder_id=payload.folder_id,
            actor_user_id=current_user.id
        )
    except EvaluationRunNotFoundError as exc:
        raise _evaluation_not_found() from exc
    except ResourceFolderNotFoundError as exc:
        raise _folder_not_found(exc) from exc
    return EvaluationRunResponse.model_validate(run)


@router.delete("/{evaluation_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_evaluation(
    evaluation_id: EvaluationId,
    workspace: ResourceDeleteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        EvaluationRunner(db).archive_run(
            workspace_id=workspace.id, run_id=evaluation_id, actor_user_id=current_user.id)
    except EvaluationRunNotFoundError as exc:
        raise _evaluation_not_found() from exc


@router.delete("/{evaluation_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def permanently_delete_evaluation(
    evaluation_id: EvaluationId,
    workspace: ResourceDeleteAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        EvaluationRunner(db).delete_archived_run(
            workspace_id=workspace.id, run_id=evaluation_id, actor_user_id=current_user.id
        )
    except EvaluationRunNotFoundError as exc:
        raise _evaluation_not_found() from exc
    except EvaluationRunActiveError as exc:
        raise HTTPException(status_code=409, detail={
            "code": "evaluation_running", "message": str(exc)}) from exc
    except (EvaluationReservationActive, EvaluationRunNotArchivedError) as exc:
        code = ("evaluation_reservation_active" if isinstance(exc, EvaluationReservationActive)
                else "evaluation_not_archived")
        raise HTTPException(status_code=409, detail={"code": code, "message": str(exc)}) from exc


def _evaluation_not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={
        "code": "evaluation_not_found", "message": "Evaluation was not found."})


def _folder_not_found(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "resource_folder_not_found", "message": "Resource folder was not found."},
    )


def _detail_response(run, *, db: Session) -> EvaluationDetailResponse:
    prompt_evidence = _prompt_version_evidence(
        db=db,
        workspace_id=run.workspace_id,
        graph_run_ids=[result.graph_run_id for result in run.results if result.graph_run_id],
    )
    return EvaluationDetailResponse(
        run=EvaluationRunResponse.model_validate(run),
        results=[
            EvaluationResultResponse.model_validate(result).model_copy(
                update={"prompt_versions": prompt_evidence.get(result.graph_run_id, [])}
            )
            for result in run.results
        ],
        metrics=[EvaluationMetricResponse.model_validate(metric) for metric in run.metrics],
    )


def _prompt_version_evidence(
    *, db: Session, workspace_id: UUID, graph_run_ids: list[UUID]
) -> dict[UUID, list[EvaluationPromptVersionResponse]]:
    if not graph_run_ids:
        return {}

    ai_runs = list(
        db.scalars(
            select(AIRun)
            .options(joinedload(AIRun.prompt_template))
            .where(AIRun.workspace_id == workspace_id, AIRun.graph_run_id.in_(graph_run_ids))
            .order_by(AIRun.graph_run_id.asc(), AIRun.created_at.asc())
        ).all()
    )
    grouped: dict[
        tuple[UUID, UUID | None, str | None, int | None, str, str, str, str],
        dict[str, object],
    ] = {}
    for ai_run in ai_runs:
        if ai_run.graph_run_id is None:
            continue
        prompt_template = ai_run.prompt_template
        language = getattr(ai_run.language, "value", str(ai_run.language))
        key = (
            ai_run.graph_run_id,
            ai_run.prompt_template_id,
            prompt_template.name if prompt_template else None,
            ai_run.prompt_version,
            language,
            ai_run.purpose,
            ai_run.provider,
            ai_run.model,
        )
        entry = grouped.setdefault(
            key,
            {
                "prompt_template_id": ai_run.prompt_template_id,
                "prompt_template_name": prompt_template.name if prompt_template else None,
                "prompt_version": ai_run.prompt_version,
                "language": language,
                "purpose": ai_run.purpose,
                "provider": ai_run.provider,
                "model": ai_run.model,
                "ai_run_count": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
            },
        )
        entry["ai_run_count"] = int(entry["ai_run_count"]) + 1
        entry["prompt_tokens"] = int(entry["prompt_tokens"]) + ai_run.prompt_tokens
        entry["completion_tokens"] = int(entry["completion_tokens"]) + ai_run.completion_tokens
        entry["total_tokens"] = int(entry["total_tokens"]) + ai_run.total_tokens
        entry["estimated_cost"] = float(entry["estimated_cost"]) + ai_run.estimated_cost

    evidence_by_graph_run: dict[UUID, list[EvaluationPromptVersionResponse]] = {}
    for key, entry in grouped.items():
        graph_run_id = key[0]
        evidence_by_graph_run.setdefault(graph_run_id, []).append(
            EvaluationPromptVersionResponse(**entry)
        )
    for evidence in evidence_by_graph_run.values():
        evidence.sort(key=lambda item: (item.purpose, item.prompt_template_name or ""))
    return evidence_by_graph_run
