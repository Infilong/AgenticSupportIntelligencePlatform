from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import GraphStepStatus, ToolCall


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    framework: str
    enabled: bool
    permissions: list[str]
    timeout_ms: int | None
    retry_policy: str
    input_schema: dict[str, object]
    output_schema: dict[str, object]
    related_workflow_nodes: list[str]


@dataclass(frozen=True)
class ToolUsageSummary:
    total_calls: int
    failed_calls: int
    average_latency_ms: float
    last_used_at: datetime | None


@dataclass(frozen=True)
class ToolCallSummary:
    id: UUID
    graph_run_id: UUID
    graph_step_id: UUID
    status: str
    latency_ms: int
    result_summary: str
    created_at: datetime


@dataclass(frozen=True)
class ToolCatalogItem:
    definition: ToolDefinition
    usage: ToolUsageSummary
    recent_calls: list[ToolCallSummary]


RUNTIME_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="search_documents",
        description=(
            "Search workspace-scoped support knowledge with hybrid retrieval and return "
            "cited chunks for the LangGraph retrieve_evidence node."
        ),
        framework="langchain_core.tools.StructuredTool",
        enabled=True,
        permissions=["workspace:read", "knowledge:write", "agents:run"],
        timeout_ms=None,
        retry_policy="No automatic retry in v1; failures are persisted in graph step/tool state.",
        input_schema={
            "type": "object",
            "required": ["query", "language"],
            "properties": {
                "query": {"type": "string", "description": "User support request."},
                "language": {"type": "string", "enum": ["en", "ja", "zh"]},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 8, "default": 4},
                "min_score": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.2},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "trace_id": {"type": "string"},
                "result_count": {"type": "integer"},
                "no_source": {"type": "boolean"},
                "results": {"type": "array", "description": "Cited retrieved chunks."},
            },
        },
        related_workflow_nodes=["retrieve_evidence"],
    )
]


class ToolService:
    def __init__(self, db: Session):
        self.db = db

    def list_tools(self, *, workspace_id: UUID) -> list[ToolCatalogItem]:
        definitions_by_name = {
            definition.name: definition for definition in RUNTIME_TOOL_DEFINITIONS
        }
        discovered_names = {
            name
            for name in self.db.scalars(
                select(ToolCall.tool_name).where(ToolCall.workspace_id == workspace_id).distinct()
            ).all()
        }
        for name in sorted(discovered_names - definitions_by_name.keys()):
            definitions_by_name[name] = _discovered_tool_definition(name)

        return [
            ToolCatalogItem(
                definition=definition,
                usage=self._usage(workspace_id=workspace_id, tool_name=definition.name),
                recent_calls=self._recent_calls(
                    workspace_id=workspace_id, tool_name=definition.name
                ),
            )
            for definition in sorted(definitions_by_name.values(), key=lambda item: item.name)
        ]

    def _usage(self, *, workspace_id: UUID, tool_name: str) -> ToolUsageSummary:
        total_calls = self.db.scalar(
            select(func.count(ToolCall.id)).where(
                ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name
            )
        ) or 0
        failed_calls = self.db.scalar(
            select(func.count(ToolCall.id)).where(
                ToolCall.workspace_id == workspace_id,
                ToolCall.tool_name == tool_name,
                ToolCall.status == GraphStepStatus.failed,
            )
        ) or 0
        average_latency = self.db.scalar(
            select(func.coalesce(func.avg(ToolCall.latency_ms), 0.0)).where(
                ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name
            )
        ) or 0.0
        last_used_at = self.db.scalar(
            select(func.max(ToolCall.created_at)).where(
                ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name
            )
        )
        return ToolUsageSummary(
            total_calls=int(total_calls),
            failed_calls=int(failed_calls),
            average_latency_ms=round(float(average_latency), 2),
            last_used_at=last_used_at,
        )

    def _recent_calls(self, *, workspace_id: UUID, tool_name: str) -> list[ToolCallSummary]:
        calls = list(
            self.db.scalars(
                select(ToolCall)
                .where(ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name)
                .order_by(ToolCall.created_at.desc())
                .limit(8)
            ).all()
        )
        return [
            ToolCallSummary(
                id=call.id,
                graph_run_id=call.graph_run_id,
                graph_step_id=call.graph_step_id,
                status=str(call.status),
                latency_ms=call.latency_ms,
                result_summary=_tool_result_summary(call.output_json),
                created_at=call.created_at,
            )
            for call in calls
        ]


def _tool_result_summary(output_json: str) -> str:
    try:
        output = json.loads(output_json)
    except json.JSONDecodeError:
        return "Unparseable tool output"
    if not isinstance(output, dict):
        return "Tool output recorded"
    if output.get("no_source") is True:
        return "No source returned"
    result_count = output.get("result_count")
    if result_count is not None:
        return f"{result_count} result(s) returned"
    return "Tool output recorded"


def _discovered_tool_definition(name: str) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        description="Runtime-discovered tool from persisted tool calls.",
        framework="unknown",
        enabled=True,
        permissions=["workspace:read", "agents:run"],
        timeout_ms=None,
        retry_policy="Unknown; discovered from historical tool calls.",
        input_schema={},
        output_schema={},
        related_workflow_nodes=[],
    )
