from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_permission
from app.models.workspace import Workspace
from app.schemas.audit import AuditLogResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/workspaces/{workspace_id}/audit-logs", tags=["audit-logs"])
DbSession = Annotated[Session, Depends(get_db)]
AuditReadAccess = Annotated[Workspace, Depends(require_workspace_permission("audit:read"))]
AuditActorFilter = Annotated[Literal["all", "user", "system"], Query()]
AuditImpactFilter = Annotated[Literal["all", "low", "medium", "high"], Query()]
AuditSearchFilter = Annotated[str | None, Query(max_length=160)]
AuditLimit = Annotated[int, Query(ge=1, le=200)]
AuditOffset = Annotated[int, Query(ge=0)]


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    workspace: AuditReadAccess,
    db: DbSession,
    search: AuditSearchFilter = None,
    actor: AuditActorFilter = "all",
    impact: AuditImpactFilter = "all",
    limit: AuditLimit = 100,
    offset: AuditOffset = 0,
) -> list[AuditLogResponse]:
    logs = AuditLogService(db).list_logs(
        workspace_id=workspace.id,
        limit=limit,
        offset=offset,
        search=search,
        actor=actor,
        impact=impact,
    )
    return [AuditLogResponse.model_validate(log) for log in logs]
