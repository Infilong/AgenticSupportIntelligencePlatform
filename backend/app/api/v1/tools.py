from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_owner
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.tool import (
    ToolCallSummaryResponse,
    ToolCatalogItemResponse,
    ToolConfigUpdateRequest,
    ToolUsageSummaryResponse,
)
from app.services.audit_log_service import AuditLogService
from app.services.tool_service import ToolCatalogItem, ToolConfigNotFoundError, ToolService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["tools"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
WorkspaceOwnerAccess = Annotated[Workspace, Depends(require_workspace_owner)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ToolName = Annotated[str, Path(min_length=1, max_length=120)]


@router.get("/tools", response_model=list[ToolCatalogItemResponse])
def list_tools(workspace: WorkspaceMemberAccess, db: DbSession) -> list[ToolCatalogItemResponse]:
    tools = ToolService(db).list_tools(workspace_id=workspace.id)
    return [_tool_response(tool) for tool in tools]


@router.patch("/tools/{tool_name}/config", response_model=ToolCatalogItemResponse)
def update_tool_config(
    tool_name: ToolName,
    payload: ToolConfigUpdateRequest,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> ToolCatalogItemResponse:
    try:
        definition = ToolService(db).update_tool_config(
            workspace_id=workspace.id,
            tool_name=tool_name,
            enabled=payload.enabled,
            timeout_ms=payload.timeout_ms,
            max_retries=payload.max_retries,
            update_timeout="timeout_ms" in payload.model_fields_set,
        )
    except ToolConfigNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "tool_not_found", "message": "Tool was not found."},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="tool_config.updated",
        resource_type="tool",
        resource_id=tool_name,
        metadata={
            "enabled": definition.enabled,
            "timeout_ms": definition.timeout_ms,
            "max_retries": definition.max_retries,
        },
    )
    tool = next(
        item
        for item in ToolService(db).list_tools(workspace_id=workspace.id)
        if item.definition.name == tool_name
    )
    return _tool_response(tool)


def _tool_response(tool: ToolCatalogItem) -> ToolCatalogItemResponse:
    definition = tool.definition
    return ToolCatalogItemResponse(
        name=definition.name,
        description=definition.description,
        framework=definition.framework,
        enabled=definition.enabled,
        permissions=definition.permissions,
        timeout_ms=definition.timeout_ms,
        max_retries=definition.max_retries,
        retry_policy=definition.retry_policy,
        input_schema=definition.input_schema,
        output_schema=definition.output_schema,
        related_workflow_nodes=definition.related_workflow_nodes,
        usage=ToolUsageSummaryResponse(
            total_calls=tool.usage.total_calls,
            failed_calls=tool.usage.failed_calls,
            average_latency_ms=tool.usage.average_latency_ms,
            last_used_at=tool.usage.last_used_at,
        ),
        recent_calls=[
            ToolCallSummaryResponse(
                id=call.id,
                graph_run_id=call.graph_run_id,
                graph_step_id=call.graph_step_id,
                status=call.status,
                latency_ms=call.latency_ms,
                result_summary=call.result_summary,
                created_at=call.created_at,
            )
            for call in tool.recent_calls
        ],
    )
