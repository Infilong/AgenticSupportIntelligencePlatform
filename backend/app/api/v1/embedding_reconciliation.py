from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.workspace import CurrentUser, DbSession, require_workspace_permission
from app.models.workspace import Workspace
from app.schemas.embedding_reconciliation import (
    EmbeddingAttemptList,
    EmbeddingAttemptResponse,
    EmbeddingReconcileRequest,
    EmbeddingRecoverRequest,
)
from app.services.embedding_reconciliation import (
    ReconciliationError,
    reconcile_attempt,
    unresolved_attempts,
)
from app.services.embedding_recovery import recover_attempt

router = APIRouter(prefix="/workspaces/{workspace_id}/embedding-attempts", tags=["costs"])
ReadAccess = Annotated[Workspace, Depends(require_workspace_permission("costs:read"))]
ManageAccess = Annotated[Workspace, Depends(require_workspace_permission("budget_policy:manage"))]


@router.post("/{attempt_id}/recover", response_model=EmbeddingAttemptResponse)
def recover(attempt_id: UUID, payload: EmbeddingRecoverRequest,
            workspace: ManageAccess, current_user: CurrentUser, db: DbSession):
    try:
        return recover_attempt(db, workspace_id=workspace.id, attempt_id=attempt_id,
                               actor_id=current_user.id, reason=payload.reason)
    except ReconciliationError as exc:
        messages = {
            "embedding_attempt_not_found": "Embedding attempt was not found.",
            "embedding_recovery_unsupported": "This attempt has no supported execution ownership.",
            "embedding_recovery_requires_postgresql": "Recovery requires PostgreSQL ownership.",
            "embedding_execution_live": "Execution is still owned; recovery was not applied.",
            "embedding_attempt_not_pending": "Only pending attempts can be recovered.",
            "embedding_recovery_forbidden": "Current membership cannot recover usage.",
            "workspace_not_found": "Workspace was not found.",
            "workspace_archived": "Restore the workspace before recovering execution.",
        }
        raise HTTPException(status_code=exc.status_code,
                            detail={"code": exc.code, "message": messages[exc.code]}) from exc


@router.get("", response_model=EmbeddingAttemptList)
def list_attempts(workspace: ReadAccess, db: DbSession,
                  limit: Annotated[int, Query(ge=1, le=100)] = 20,
                  offset: Annotated[int, Query(ge=0)] = 0) -> EmbeddingAttemptList:
    rows = unresolved_attempts(db, workspace_id=workspace.id, limit=limit, offset=offset)
    return EmbeddingAttemptList(items=[EmbeddingAttemptResponse.model_validate(row)
                                      for row in rows[:limit]], has_more=len(rows) > limit)


@router.post("/{attempt_id}/reconcile", response_model=EmbeddingAttemptResponse)
def reconcile(attempt_id: UUID, payload: EmbeddingReconcileRequest,
              workspace: ManageAccess, current_user: CurrentUser, db: DbSession):
    try:
        return reconcile_attempt(db, workspace_id=workspace.id, attempt_id=attempt_id,
                                 actor_id=current_user.id, payload=payload)
    except ReconciliationError as exc:
        messages = {
            "workspace_not_found": "Workspace was not found.",
            "workspace_archived": "Restore the workspace before reconciling usage.",
            "embedding_attempt_not_found": "Embedding attempt was not found.",
            "embedding_attempt_not_uncertain": (
                "Only uncertain attempts can be reconciled. Pending calls may still be running; "
                "already reconciled attempts cannot be changed."
            ),
            "embedding_attempt_invalid_rate": "Stored pricing is invalid; investigate the ledger.",
            "embedding_attempt_invalid_cost": "Confirmed usage produces an invalid cost.",
        }
        raise HTTPException(status_code=exc.status_code,
                            detail={"code": exc.code, "message": messages[exc.code]}) from exc
