from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_member
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent import (
    AgentCreateRequest,
    AgentResponse,
    AgentRunRequest,
    GraphRunResponse,
    GraphStepResponse,
    GraphTraceResponse,
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
    return GraphTraceResponse(
        run=GraphRunResponse.model_validate(run),
        steps=[GraphStepResponse.model_validate(step) for step in run.steps],
    )
