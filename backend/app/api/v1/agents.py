import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member, require_workspace_owner
from app.models.agent import Checkpoint
from app.models.ai import AIRun
from app.models.review import GuardrailResult
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent import (
    AgentCreateRequest,
    AgentOperationalSummaryResponse,
    AgentResponse,
    AgentRunRequest,
    AgentUpdateRequest,
    AIRunTraceResponse,
    CheckpointTraceResponse,
    GraphRunResponse,
    GraphRuntimeResponse,
    GraphStepResponse,
    GraphTraceResponse,
    GuardrailTraceResponse,
    RuntimeComponentResponse,
    ToolCallResponse,
)
from app.services.agent_service import (
    AgentNotFoundError,
    AgentService,
    AgentUnavailableError,
    GraphRunNotFoundError,
)
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["agents"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
WorkspaceOwnerAccess = Annotated[Workspace, Depends(require_workspace_owner)]
CurrentUser = Annotated[User, Depends(get_current_user)]
IncludeArchived = Annotated[bool, Query()]
AgentId = Annotated[UUID, Path()]
RunId = Annotated[UUID, Path()]


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreateRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    agent = AgentService(db).create_agent(
        workspace_id=workspace.id, name=payload.name, token_budget=payload.token_budget
    )
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="agent.created",
        resource_type="agent",
        resource_id=agent.id,
        metadata={"name": agent.name, "token_budget": agent.token_budget},
    )
    return AgentResponse.model_validate(agent)


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(
    workspace: WorkspaceMemberAccess,
    db: DbSession,
    include_archived: IncludeArchived = False,
) -> list[AgentResponse]:
    agents = AgentService(db).list_agents(
        workspace_id=workspace.id, include_archived=include_archived
    )
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.get("/agents/{agent_id}/summary", response_model=AgentOperationalSummaryResponse)
def get_agent_summary(
    agent_id: AgentId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> AgentOperationalSummaryResponse:
    try:
        summary = AgentService(db).get_operational_summary(
            workspace_id=workspace.id, agent_id=agent_id
        )
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "agent_not_found", "message": "Agent was not found."},
        ) from exc
    return AgentOperationalSummaryResponse(
        agent=AgentResponse.model_validate(summary["agent"]),
        recent_runs=[GraphRunResponse.model_validate(run) for run in summary["recent_runs"]],
        total_runs=summary["total_runs"],
        completed_runs=summary["completed_runs"],
        human_review_runs=summary["human_review_runs"],
        failed_runs=summary["failed_runs"],
        total_tokens=summary["total_tokens"],
        total_estimated_cost=summary["total_estimated_cost"],
        average_ai_latency_ms=summary["average_ai_latency_ms"],
        last_run_at=summary["last_run_at"],
    )


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: AgentId,
    payload: AgentUpdateRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> AgentResponse:
    settings = {
        key: value
        for key, value in {
            "confidence_threshold": payload.confidence_threshold,
            "retrieval_top_k": payload.retrieval_top_k,
            "retrieval_min_score": payload.retrieval_min_score,
        }.items()
        if value is not None
    }
    try:
        agent = AgentService(db).update_agent(
            workspace_id=workspace.id,
            agent_id=agent_id,
            name=payload.name,
            active=payload.active,
            token_budget=payload.token_budget,
            settings=settings or None,
        )
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "agent_not_found", "message": "Agent was not found."},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="agent.updated",
        resource_type="agent",
        resource_id=agent.id,
        metadata={"name": agent.name, "token_budget": agent.token_budget},
    )
    return AgentResponse.model_validate(agent)


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_agent(
    agent_id: AgentId,
    workspace: WorkspaceOwnerAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    try:
        agent = AgentService(db).archive_agent(workspace_id=workspace.id, agent_id=agent_id)
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "agent_not_found", "message": "Agent was not found."},
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="agent.archived",
        resource_type="agent",
        resource_id=agent.id,
        metadata={
            "name": agent.name,
            "archived_at": agent.archived_at.isoformat() if agent.archived_at else None,
        },
    )


@router.post("/agents/{agent_id}/runs", response_model=GraphRunResponse, status_code=201)
def run_agent(
    agent_id: AgentId,
    payload: AgentRunRequest,
    workspace: WorkspaceMemberAccess,
    current_user: CurrentUser,
    db: DbSession,
) -> GraphRunResponse:
    try:
        run = AgentService(db).run_agent(
            workspace_id=workspace.id,
            agent_id=agent_id,
            input_message=payload.input_message,
            current_user=current_user,
        )
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "agent_not_found", "message": "Agent was not found."},
        ) from exc
    except AgentUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "agent_unavailable",
                "message": "Agent is inactive or archived and cannot be run.",
            },
        ) from exc
    AuditLogService(db).record(
        workspace_id=workspace.id,
        actor_user_id=current_user.id,
        action="agent.run_completed",
        resource_type="graph_run",
        resource_id=run.id,
        metadata={"agent_id": str(agent_id), "status": run.status},
    )
    return GraphRunResponse.model_validate(run)


@router.get("/agent-runs/{run_id}", response_model=GraphRunResponse)
def get_agent_run(
    run_id: RunId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> GraphRunResponse:
    try:
        run = AgentService(db).get_run(workspace_id=workspace.id, run_id=run_id)
    except GraphRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "graph_run_not_found", "message": "Graph run was not found."},
        ) from exc
    return GraphRunResponse.model_validate(run)


@router.get("/agent-runs/{run_id}/trace", response_model=GraphTraceResponse)
def get_agent_trace(
    run_id: RunId,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> GraphTraceResponse:
    try:
        run = AgentService(db).get_trace(workspace_id=workspace.id, run_id=run_id)
    except GraphRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "graph_run_not_found", "message": "Graph run was not found."},
        ) from exc
    ai_runs = list(
        db.scalars(
            select(AIRun)
            .options(joinedload(AIRun.prompt_template))
            .where(AIRun.workspace_id == workspace.id, AIRun.id.in_(_ai_run_ids(run.steps)))
            .order_by(AIRun.created_at.asc())
        ).all()
    )
    ai_runs_by_id = {ai_run.id: _ai_run_trace_response(ai_run) for ai_run in ai_runs}
    guardrails = list(
        db.scalars(
            select(GuardrailResult)
            .where(
                GuardrailResult.workspace_id == workspace.id,
                GuardrailResult.graph_run_id == run.id,
            )
            .order_by(GuardrailResult.created_at.asc())
        ).all()
    )
    checkpoints = list(
        db.scalars(
            select(Checkpoint).where(
                Checkpoint.workspace_id == workspace.id,
                Checkpoint.graph_run_id == run.id,
            )
        ).all()
    )
    checkpoints.sort(key=_checkpoint_sort_key)
    return GraphTraceResponse(
        runtime=_graph_runtime_response(run.steps),
        run=GraphRunResponse.model_validate(run),
        steps=[_graph_step_response(step, ai_runs_by_id.get(step.ai_run_id)) for step in run.steps],
        ai_runs=list(ai_runs_by_id.values()),
        guardrails=[GuardrailTraceResponse.model_validate(item) for item in guardrails],
        checkpoints=[CheckpointTraceResponse.model_validate(item) for item in checkpoints],
    )


def _checkpoint_sort_key(checkpoint: Checkpoint) -> tuple[int, str]:
    node_order = {
        "detect_language": 10,
        "classify_intent": 20,
        "retrieve_evidence": 30,
        "draft_response": 40,
        "score_confidence": 50,
        "route_review_or_finalize": 60,
        "finalize_response": 70,
        "human_review_approved": 80,
        "human_review_edited": 80,
        "human_review_rejected": 80,
    }
    node_name = checkpoint.checkpoint_key.removesuffix(":after")
    return (node_order.get(node_name, 999), checkpoint.checkpoint_key)


def _ai_run_ids(steps) -> list[UUID]:
    return [step.ai_run_id for step in steps if step.ai_run_id is not None]


def _ai_run_trace_response(ai_run: AIRun) -> AIRunTraceResponse:
    prompt_template = ai_run.prompt_template
    return AIRunTraceResponse.model_validate(ai_run).model_copy(
        update={
            "prompt_template_name": prompt_template.name if prompt_template else None,
            "prompt_template_text": prompt_template.template_text if prompt_template else None,
        }
    )


def _graph_step_response(step, ai_run: AIRunTraceResponse | None) -> GraphStepResponse:
    tool_calls = [_tool_call_response(tool_call) for tool_call in step.tool_calls]
    return GraphStepResponse.model_validate(step).model_copy(
        update={
            "ai_run": ai_run,
            "tool_calls": tool_calls,
            **_step_runtime_metadata(step, ai_run=ai_run, tool_calls=tool_calls),
        }
    )


def _tool_call_response(tool_call) -> ToolCallResponse:
    output = _safe_json_object(tool_call.output_json)
    return ToolCallResponse.model_validate(tool_call).model_copy(
        update={"framework": output.get("framework") if output else None}
    )


def _step_runtime_metadata(
    step, *, ai_run: AIRunTraceResponse | None, tool_calls: list[ToolCallResponse]
) -> dict:
    input_state = _safe_json_object(step.input_json)
    output_state = _safe_json_object(step.output_json)
    state_keys = sorted(set(input_state.keys()) | set(output_state.keys()))
    uses_langchain = bool(ai_run) or any(
        (tool.framework or "").startswith("langchain") for tool in tool_calls
    )
    return {
        "runtime_framework": "LangGraph StateGraph node",
        "node_role": _node_role(step.step_name),
        "uses_langchain": uses_langchain,
        "state_keys": state_keys,
    }


def _graph_runtime_response(steps) -> GraphRuntimeResponse:
    return GraphRuntimeResponse(
        orchestrator="LangGraph StateGraph",
        state_schema="SupportAgentState TypedDict",
        graph_builder="app.services.support_agent_graph.SupportAgentGraphRunner",
        execution_mode="deterministic graph with conditional human-review routing",
        node_count=len(steps),
        conditional_routes=[
            "route_review_or_finalize -> finalize_response",
            "route_review_or_finalize -> human_review",
        ],
        persistence=[
            "GraphStep",
            "Checkpoint",
            "ToolCall",
            "AIRun",
            "RetrievalTrace",
            "GuardrailResult",
        ],
        langchain_components=[
            RuntimeComponentResponse(
                name="ChatPromptTemplate",
                framework="LangChain Core",
                role="versioned classification and draft-response prompt assembly",
            ),
            RuntimeComponentResponse(
                name="RunnableLambda + StrOutputParser",
                framework="LangChain Core",
                role="LCEL model-provider bridge and normalized text output parsing",
            ),
            RuntimeComponentResponse(
                name="Document",
                framework="LangChain Core",
                role="cited retrieval chunks converted into prompt evidence objects",
            ),
            RuntimeComponentResponse(
                name="StructuredTool search_documents",
                framework="LangChain Core",
                role="workspace-scoped retrieval tool invoked by the retrieve_evidence node",
            ),
        ],
    )


def _node_role(step_name: str) -> str:
    roles = {
        "detect_language": "deterministic language detection",
        "classify_intent": "LangChain classification chain with cheap model config",
        "retrieve_evidence": "LangChain retrieval tool plus persisted retrieval trace",
        "draft_response": "LangChain grounded drafting chain with cited documents",
        "score_confidence": "deterministic confidence scoring",
        "route_review_or_finalize": "conditional LangGraph routing gate",
        "finalize_response": "final response commit",
    }
    return roles.get(step_name, "workflow step")


def _safe_json_object(raw: str) -> dict:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
