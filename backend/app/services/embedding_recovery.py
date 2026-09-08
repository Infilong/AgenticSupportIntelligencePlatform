"""Audited orphan transition; ownership loss never implies zero provider usage."""

import json
from uuid import UUID

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.workspace import Workspace, WorkspaceMember
from app.services.embedding_reconciliation import EMBEDDING_PURPOSES, ReconciliationError
from app.services.execution_ownership import ExecutionBusy, own_execution
from app.services.workspace_service import permissions_for_role


def recover_attempt(db: Session, *, workspace_id: UUID, attempt_id: UUID,
                    actor_id: UUID, reason: str) -> AIRun:
    attempt = db.scalar(select(AIRun).where(
        AIRun.workspace_id == workspace_id, AIRun.id == attempt_id,
        AIRun.provider == "openai", AIRun.purpose.in_(EMBEDDING_PURPOSES)))
    if attempt is None:
        raise ReconciliationError("embedding_attempt_not_found", 404)
    execution_id = attempt.execution_id
    if execution_id is None or attempt.execution_protocol != "pg-session-v1":
        raise ReconciliationError("embedding_recovery_unsupported", 409)
    engine = db.get_bind()
    if not isinstance(engine, Engine) or engine.dialect.name != "postgresql":
        raise ReconciliationError("embedding_recovery_requires_postgresql", 409)
    try:
        with own_execution(engine, workspace_id=workspace_id, execution_id=execution_id) as owner:
            with Session(owner.connection, expire_on_commit=False) as transaction:
                transaction.connection()
                owner.assert_owned()
                workspace = transaction.scalar(select(Workspace).where(Workspace.id == workspace_id)
                    .with_for_update(key_share=True))
                if workspace is None or workspace.deleted_at is not None:
                    raise ReconciliationError("workspace_not_found", 404)
                if workspace.archived_at is not None:
                    raise ReconciliationError("workspace_archived", 409)
                member = transaction.scalar(select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == actor_id).with_for_update(read=True))
                if (member is None or
                        "budget_policy:manage" not in permissions_for_role(member.role)):
                    raise ReconciliationError("embedding_recovery_forbidden", 403)
                current = transaction.scalar(select(AIRun).where(
                    AIRun.workspace_id == workspace_id, AIRun.id == attempt_id,
                    AIRun.provider == "openai", AIRun.purpose.in_(EMBEDDING_PURPOSES),
                    AIRun.execution_id == execution_id,
                    AIRun.execution_protocol == "pg-session-v1").with_for_update())
                if current is None:
                    raise ReconciliationError("embedding_attempt_not_found", 404)
                if current.status != AIRunStatus.pending:
                    raise ReconciliationError("embedding_attempt_not_pending", 409)
                previous_error = current.error_message
                current.status = AIRunStatus.uncertain
                current.error_message = "embedding_orphaned_usage_requires_reconciliation"
                transaction.add(AuditLog(workspace_id=workspace_id, actor_user_id=actor_id,
                    action="embedding_execution.recovered", resource_type="ai_run",
                    resource_id=str(attempt_id), metadata_json=json.dumps({
                        "execution_id": str(execution_id), "previous_status": "pending",
                        "status": "uncertain", "previous_error": previous_error,
                        "retained_tokens": current.total_tokens,
                        "retained_estimated_cost": current.estimated_cost, "reason": reason,
                    })))
                transaction.commit()
                return current
    except ExecutionBusy as exc:
        raise ReconciliationError("embedding_execution_live", 409) from exc
