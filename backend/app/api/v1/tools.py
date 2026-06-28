from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
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
ToolReadAccess = Annotated[Workspace, Depends(require_workspace_permission("tools:read"))]
ToolConfigureAccess = Annotated[Workspace, Depends(require_workspace_permission("tools:configure"))]
CurrentUser = Annotated[User, Depends(get_current_user)]
ToolName = Annotated[str, Path(min_length=1, max_length=120)]
ToolSearch = Annotated[str | None, Query(max_length=240)]
ToolViewFilter = Annotated[Literal["all", "enabled", "disabled", "failed", "configured"], Query()]
ListLimit = Annotated[int, Query(ge=1, le=100)]
ListOffset = Annotated[int, Query(ge=0)]


@router.get("/tools", response_model=list[ToolCatalogItemResponse])
def list_tools(
    workspace: ToolReadAccess,
    db: DbSession,
    search: ToolSearch = None,
    view: ToolViewFilter = "all",
    limit: ListLimit = 30,
    offset: ListOffset = 0,
) -> list[ToolCatalogItemResponse]:
    tools = ToolService(db).list_tools(
        workspace_id=workspace.id, search=search, view=view, limit=limit, offset=offset
    )
    return [_tool_response(tool) for tool in tools]


@router.patch("/tools/{tool_name}/config", response_model=ToolCatalogItemResponse)
def update_tool_config(
    tool_name: ToolName,
    payload: ToolConfigUpdateRequest,
    workspace: ToolConfigureAccess,
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
                step_name=call.step_name,
                graph_run_status=call.graph_run_status,
                graph_run_input_message=call.graph_run_input_message,
                graph_run_language=call.graph_run_language,
                status=call.status,
                latency_ms=call.latency_ms,
                input_json=call.input_json,
                output_json=call.output_json,
                error_message=call.error_message,
                result_summary=call.result_summary,
                created_at=call.created_at,
            )
            for call in tool.recent_calls
        ],
    )
