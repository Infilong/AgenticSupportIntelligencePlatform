"""Own evaluation management and attributable audit persistence in one transaction."""

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.audit import AuditLog
from app.models.evaluation import EvaluationCase, EvaluationRun, EvaluationRunStatus
from app.services.budget_reservations import BudgetReservationService
from app.services.folder_service import ResourceFolderService


class EvaluationRunNotFoundError(ValueError):
    pass


class EvaluationRunNotArchivedError(ValueError):
    pass


class EvaluationRunActiveError(ValueError):
    pass


class EvaluationManagement:
    def __init__(self, db: Session):
        self.db = db

    def move_run(
        self, *, workspace_id: UUID, run_id: UUID, folder_id: UUID | None, actor_user_id: UUID
    ) -> EvaluationRun:
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="evaluation_run"
        )
        run = self.db.scalar(
            select(EvaluationRun).where(
                EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id
            )
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        run.folder_id = folder_id
        self._commit(run, actor_user_id, "moved")
        self.db.refresh(run)
        return run

    def archive_run(self, *, workspace_id: UUID, run_id: UUID,
                    actor_user_id: UUID) -> EvaluationRun:
        run = self.db.scalar(
            select(EvaluationRun).where(
                EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id
            )
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        if run.archived_at is None:
            run.archived_at = datetime.now(UTC)
        self._commit(run, actor_user_id, "archived")
        self.db.refresh(run)
        return run

    def delete_archived_run(self, *, workspace_id: UUID, run_id: UUID,
                    actor_user_id: UUID) -> EvaluationRun:
        run = self.db.scalar(
            select(EvaluationRun)
            .options(selectinload(EvaluationRun.results), selectinload(EvaluationRun.metrics))
            .where(EvaluationRun.workspace_id == workspace_id, EvaluationRun.id == run_id)
        )
        if run is None:
            raise EvaluationRunNotFoundError("Evaluation run was not found.")
        if run.archived_at is None:
            raise EvaluationRunNotArchivedError(
                "Archive the evaluation run before permanent deletion."
            )
        BudgetReservationService(self.db).guard_evaluation_delete(workspace_id, run_id)
        if run.status == EvaluationRunStatus.running:
            raise EvaluationRunActiveError(
                "Evaluation is still running; permanent deletion is blocked.")
        case_ids = [result.evaluation_case_id for result in run.results]
        for metric in list(run.metrics):
            self.db.delete(metric)
        for result in list(run.results):
            self.db.delete(result)
        for case_id in case_ids:
            case = self.db.scalar(
                select(EvaluationCase).where(
                    EvaluationCase.workspace_id == workspace_id,
                    EvaluationCase.id == case_id,
                )
            )
            if case is not None:
                self.db.delete(case)
        self.db.delete(run)
        self._commit(run, actor_user_id, "deleted")
        return run

    def _commit(self, run: EvaluationRun, actor: UUID, action: str) -> None:
        metadata = {"name": run.name}
        if action == "moved":
            metadata = {"folder_id": str(run.folder_id) if run.folder_id else None}
        elif action == "archived":
            metadata["archived_at"] = run.archived_at.isoformat() if run.archived_at else None
        try:
            self.db.flush()
            self.db.add(AuditLog(
                workspace_id=run.workspace_id, actor_user_id=actor,
                action=f"evaluation.{action}", resource_type="evaluation_run",
                resource_id=str(run.id),
                metadata_json=json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            ))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
