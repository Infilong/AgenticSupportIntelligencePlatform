from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.audit import AuditLogResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/workspaces/{workspace_id}/audit-logs", tags=["audit-logs"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    workspace: WorkspaceMemberAccess,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[AuditLogResponse]:
    logs = AuditLogService(db).list_logs(workspace_id=workspace.id, limit=limit)
    return [AuditLogResponse.model_validate(log) for log in logs]
