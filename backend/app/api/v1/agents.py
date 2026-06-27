from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.ai import AIRun
from app.models.review import GuardrailResult
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent import (
    AgentCreateRequest,
    AgentResponse,
    AgentRunRequest,
    AgentUpdateRequest,
    AIRunTraceResponse,
    GraphRunResponse,
    GraphStepResponse,
    GraphTraceResponse,
    GuardrailTraceResponse,
)
from app.services.agent_service import AgentNotFoundError, AgentService, GraphRunNotFoundError

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["agents"])
DbSession = Annotated[Session, Depends(get_db)]
WorkspaceMemberAccess = Annotated[Workspace, Depends(require_workspace_member)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AgentId = Annotated[UUID, Path()]
RunId = Annotated[UUID, Path()]


@router.post("/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    payload: AgentCreateRequest,
    workspace: WorkspaceMemberAccess,
    db: DbSession,
) -> AgentResponse:
    agent = AgentService(db).create_agent(
        workspace_id=workspace.id, name=payload.name, token_budget=payload.token_budget
    )
    return AgentResponse.model_validate(agent)


@router.get("/agents", response_model=list[AgentResponse])
def list_agents(workspace: WorkspaceMemberAccess, db: DbSession) -> list[AgentResponse]:
    agents = AgentService(db).list_agents(workspace_id=workspace.id)
    return [AgentResponse.model_validate(agent) for agent in agents]


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: AgentId,
    payload: AgentUpdateRequest,
    workspace: WorkspaceMemberAccess,
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
    return AgentResponse.model_validate(agent)


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
    return GraphTraceResponse(
        run=GraphRunResponse.model_validate(run),
        steps=[
            GraphStepResponse.model_validate(step).model_copy(
                update={"ai_run": ai_runs_by_id.get(step.ai_run_id)}
            )
            for step in run.steps
        ],
        ai_runs=list(ai_runs_by_id.values()),
        guardrails=[GuardrailTraceResponse.model_validate(item) for item in guardrails],
    )


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
