from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.workspace import require_workspace_member
from app.models.workspace import Workspace
from app.schemas.tool import (
    ToolCallSummaryResponse,
    ToolCatalogItemResponse,
    ToolUsageSummaryResponse,
)
from app.services.tool_service import ToolCatalogItem, ToolService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["tools"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]


@router.get("/tools", response_model=list[ToolCatalogItemResponse])
def list_tools(workspace: WorkspaceMemberAccess, db: DbSession) -> list[ToolCatalogItemResponse]:
    tools = ToolService(db).list_tools(workspace_id=workspace.id)
    return [_tool_response(tool) for tool in tools]


def _tool_response(tool: ToolCatalogItem) -> ToolCatalogItemResponse:
    definition = tool.definition
    return ToolCatalogItemResponse(
        name=definition.name,
        description=definition.description,
        framework=definition.framework,
        enabled=definition.enabled,
        permissions=definition.permissions,
        timeout_ms=definition.timeout_ms,
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
