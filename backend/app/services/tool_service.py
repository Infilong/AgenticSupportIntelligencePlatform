from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphStep, GraphStepStatus, ToolCall
from app.models.tool import ToolConfig


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    framework: str
    enabled: bool
    permissions: list[str]
    timeout_ms: int | None
    max_retries: int
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
    step_name: str
    graph_run_status: str
    graph_run_input_message: str
    graph_run_language: str | None
    status: str
    latency_ms: int
    input_json: str
    output_json: str
    error_message: str | None
    result_summary: str
    created_at: datetime


@dataclass(frozen=True)
class ToolCatalogItem:
    definition: ToolDefinition
    usage: ToolUsageSummary
    recent_calls: list[ToolCallSummary]


class ToolConfigNotFoundError(ValueError):
    pass


RUNTIME_TOOL_DEFINITIONS = [
    ToolDefinition(
        name="search_documents",
        description=(
            "Search workspace-scoped support knowledge with hybrid retrieval and return "
            "cited chunks for the LangGraph retrieve_evidence node."
        ),
        framework="langchain_core.tools.StructuredTool",
        enabled=True,
        permissions=["workspace:read", "knowledge:read", "agents:run"],
        timeout_ms=None,
        max_retries=0,
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

    def list_tools(
        self,
        *,
        workspace_id: UUID,
        search: str | None = None,
        view: str = "all",
        limit: int = 30,
        offset: int = 0,
    ) -> list[ToolCatalogItem]:
        filtered = self._filtered_tools(workspace_id=workspace_id, search=search, view=view)
        start = max(offset, 0)
        return filtered[start : start + _bounded_limit(limit)]

    def count_tools(
        self,
        *,
        workspace_id: UUID,
        search: str | None = None,
        view: str = "all",
    ) -> int:
        return len(self._filtered_tools(workspace_id=workspace_id, search=search, view=view))

    def _filtered_tools(
        self, *, workspace_id: UUID, search: str | None, view: str
    ) -> list[ToolCatalogItem]:
        definitions_by_name = self._definitions_for_workspace(workspace_id=workspace_id)
        items = [
            ToolCatalogItem(
                definition=definition,
                usage=self._usage(workspace_id=workspace_id, tool_name=definition.name),
                recent_calls=self._recent_calls(
                    workspace_id=workspace_id, tool_name=definition.name
                ),
            )
            for definition in sorted(definitions_by_name.values(), key=lambda item: item.name)
        ]
        return [
            item
            for item in items
            if _tool_matches_view(item, view) and _tool_matches_search(item, search)
        ]

    def get_tool_definition(self, *, workspace_id: UUID, tool_name: str) -> ToolDefinition:
        definition = self._definitions_for_workspace(workspace_id=workspace_id).get(tool_name)
        if definition is None:
            raise ToolConfigNotFoundError("Tool was not found.")
        return definition

    def update_tool_config(
        self,
        *,
        workspace_id: UUID,
        tool_name: str,
        enabled: bool | None = None,
        timeout_ms: int | None = None,
        max_retries: int | None = None,
        update_timeout: bool = False,
    ) -> ToolDefinition:
        base_definition = self._base_definitions(workspace_id=workspace_id).get(tool_name)
        if base_definition is None:
            raise ToolConfigNotFoundError("Tool was not found.")
        config = self.db.scalar(
            select(ToolConfig).where(
                ToolConfig.workspace_id == workspace_id, ToolConfig.tool_name == tool_name
            )
        )
        if config is None:
            config = ToolConfig(
                workspace_id=workspace_id,
                tool_name=tool_name,
                enabled=base_definition.enabled,
                timeout_ms=base_definition.timeout_ms,
                max_retries=base_definition.max_retries,
            )
            self.db.add(config)
            self.db.flush()
        if enabled is not None:
            config.enabled = enabled
        if update_timeout:
            config.timeout_ms = timeout_ms
        if max_retries is not None:
            config.max_retries = max_retries
        self.db.commit()
        return self.get_tool_definition(workspace_id=workspace_id, tool_name=tool_name)

    def _definitions_for_workspace(self, *, workspace_id: UUID) -> dict[str, ToolDefinition]:
        definitions_by_name = self._base_definitions(workspace_id=workspace_id)
        configs = {
            config.tool_name: config
            for config in self.db.scalars(
                select(ToolConfig).where(ToolConfig.workspace_id == workspace_id)
            ).all()
        }
        return {
            name: _apply_config(definition, configs.get(name))
            for name, definition in definitions_by_name.items()
        }

    def _base_definitions(self, *, workspace_id: UUID) -> dict[str, ToolDefinition]:
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
        return definitions_by_name

    def _usage(self, *, workspace_id: UUID, tool_name: str) -> ToolUsageSummary:
        total_calls = (
            self.db.scalar(
                select(func.count(ToolCall.id)).where(
                    ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name
                )
            )
            or 0
        )
        failed_calls = (
            self.db.scalar(
                select(func.count(ToolCall.id)).where(
                    ToolCall.workspace_id == workspace_id,
                    ToolCall.tool_name == tool_name,
                    ToolCall.status == GraphStepStatus.failed,
                )
            )
            or 0
        )
        average_latency = (
            self.db.scalar(
                select(func.coalesce(func.avg(ToolCall.latency_ms), 0.0)).where(
                    ToolCall.workspace_id == workspace_id, ToolCall.tool_name == tool_name
                )
            )
            or 0.0
        )
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
        rows = list(
            self.db.execute(
                select(ToolCall, GraphStep, GraphRun)
                .join(GraphStep, ToolCall.graph_step_id == GraphStep.id)
                .join(GraphRun, ToolCall.graph_run_id == GraphRun.id)
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
                step_name=step.step_name,
                graph_run_status=str(run.status),
                graph_run_input_message=run.input_message,
                graph_run_language=str(run.language) if run.language else None,
                status=str(call.status),
                latency_ms=call.latency_ms,
                input_json=call.input_json,
                output_json=call.output_json,
                error_message=step.error_message,
                result_summary=_tool_result_summary(call.output_json),
                created_at=call.created_at,
            )
            for call, step, run in rows
        ]


def _apply_config(definition: ToolDefinition, config: ToolConfig | None) -> ToolDefinition:
    if config is None:
        return definition
    return ToolDefinition(
        name=definition.name,
        description=definition.description,
        framework=definition.framework,
        enabled=config.enabled,
        permissions=definition.permissions,
        timeout_ms=config.timeout_ms,
        max_retries=config.max_retries,
        retry_policy=_retry_policy(config.max_retries),
        input_schema=definition.input_schema,
        output_schema=definition.output_schema,
        related_workflow_nodes=definition.related_workflow_nodes,
    )


def _retry_policy(max_retries: int) -> str:
    if max_retries <= 0:
        return "No automatic retry; failures are persisted in graph step/tool state."
    if max_retries == 1:
        return "1 automatic retry before routing failure state to human review."
    return f"{max_retries} automatic retries before routing failure state to human review."


def _tool_result_summary(output_json: str) -> str:
    try:
        output = json.loads(output_json)
    except json.JSONDecodeError:
        return "Unparseable tool output"
    if not isinstance(output, dict):
        return "Tool output recorded"
    if output.get("tool_disabled") is True:
        return "Tool disabled by workspace config"
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
        max_retries=0,
        retry_policy="Unknown; discovered from historical tool calls.",
        input_schema={},
        output_schema={},
        related_workflow_nodes=[],
    )


def _bounded_limit(limit: int) -> int:
    return max(min(limit, 100), 1)


def _tool_matches_view(item: ToolCatalogItem, view: str) -> bool:
    definition = item.definition
    if view == "enabled":
        return definition.enabled
    if view == "disabled":
        return not definition.enabled
    if view == "failed":
        return item.usage.failed_calls > 0
    if view == "configured":
        return bool(definition.timeout_ms or definition.max_retries or not definition.enabled)
    return True


def _tool_matches_search(item: ToolCatalogItem, search: str | None) -> bool:
    query = (search or "").strip().lower()
    if not query:
        return True
    definition = item.definition
    haystack = " ".join(
        [
            definition.name,
            definition.description,
            definition.framework,
            definition.retry_policy,
            *definition.permissions,
            *definition.related_workflow_nodes,
            json.dumps(definition.input_schema, sort_keys=True),
            json.dumps(definition.output_schema, sort_keys=True),
            *[call.step_name for call in item.recent_calls],
            *[call.graph_run_input_message for call in item.recent_calls],
            *[call.status for call in item.recent_calls],
            *[call.result_summary for call in item.recent_calls],
        ]
    ).lower()
    return query in haystack
