from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_permission
from app.models.workspace import Workspace
from app.schemas.system_health import SystemHealthResponse
from app.services.system_health_service import SystemHealthService

router = APIRouter(prefix="/workspaces/{workspace_id}/system-health", tags=["system-health"])
DbSession = Annotated[Session, Depends(get_db)]
SystemReadAccess = Annotated[Workspace, Depends(require_workspace_permission("system:read"))]


@router.get("", response_model=SystemHealthResponse)
def get_system_health(workspace: SystemReadAccess, db: DbSession) -> SystemHealthResponse:
    return SystemHealthService(db).get_workspace_health(workspace_id=workspace.id)
