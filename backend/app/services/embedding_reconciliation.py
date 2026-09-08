"""Operator-confirmed billing updates; never retry or fabricate successful vectors."""

import json
import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.workspace import Workspace
from app.schemas.embedding_reconciliation import EmbeddingReconcileRequest

EMBEDDING_PURPOSES = ("embedding_document", "embedding_query")


class ReconciliationError(ValueError):
    def __init__(self, code: str, status_code: int):
        super().__init__(code)
        self.code = code
        self.status_code = status_code


def unresolved_attempts(db: Session, *, workspace_id: UUID, limit: int, offset: int):
    return list(db.scalars(select(AIRun).where(
        AIRun.workspace_id == workspace_id, AIRun.provider == "openai",
        AIRun.purpose.in_(EMBEDDING_PURPOSES),
        AIRun.status.in_((AIRunStatus.pending, AIRunStatus.uncertain)),
    ).order_by(AIRun.created_at, AIRun.id).offset(offset).limit(limit + 1)))


def reconcile_attempt(db: Session, *, workspace_id: UUID, attempt_id: UUID,
                      actor_id: UUID, payload: EmbeddingReconcileRequest) -> AIRun:
    # This function owns the request transaction, including the audit write.
    try:
        workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id)
            .with_for_update(key_share=True).execution_options(populate_existing=True))
        if workspace is None or workspace.deleted_at is not None:
            raise ReconciliationError("workspace_not_found", 404)
        if workspace.archived_at is not None:
            raise ReconciliationError("workspace_archived", 409)
        attempt = db.scalar(select(AIRun).where(
            AIRun.workspace_id == workspace_id, AIRun.id == attempt_id,
            AIRun.provider == "openai", AIRun.purpose.in_(EMBEDDING_PURPOSES),
        ).with_for_update().execution_options(populate_existing=True))
        if attempt is None:
            raise ReconciliationError("embedding_attempt_not_found", 404)
        if attempt.status != AIRunStatus.uncertain:
            raise ReconciliationError("embedding_attempt_not_uncertain", 409)
        if (attempt.total_tokens <= 0 or not math.isfinite(attempt.estimated_cost)
                or attempt.estimated_cost <= 0):
            raise ReconciliationError("embedding_attempt_invalid_rate", 409)
        previous = {"status": attempt.status.value, "total_tokens": attempt.total_tokens,
                    "estimated_cost": attempt.estimated_cost,
                    "error_message": attempt.error_message}
        # Preserve the admission-time price, even if settings have changed since dispatch.
        cost = payload.confirmed_tokens * (attempt.estimated_cost / attempt.total_tokens)
        if not math.isfinite(cost):
            raise ReconciliationError("embedding_attempt_invalid_cost", 409)
        attempt.prompt_tokens = attempt.total_tokens = payload.confirmed_tokens
        attempt.completion_tokens = 0
        attempt.estimated_cost = cost
        attempt.status = AIRunStatus.failed
        attempt.error_message = "embedding_failed_usage_reconciled"
        db.add(AuditLog(workspace_id=workspace_id, actor_user_id=actor_id,
            action="embedding_usage.reconciled", resource_type="ai_run",
            resource_id=str(attempt.id), metadata_json=json.dumps({
                "previous": previous, "confirmed_tokens": payload.confirmed_tokens,
                "estimated_cost": cost, "status": attempt.status.value,
                "evidence_reference": payload.evidence_reference,
            })))
        db.commit()
        return attempt
    except Exception:
        # Roll back both writes and preserve the original failure for the HTTP error handler.
        db.rollback()
        raise
