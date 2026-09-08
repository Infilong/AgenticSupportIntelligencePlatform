"""Workspace-scoped inspection and exact-input human resolution of internal actions."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.agent import GraphRun
from app.models.task_action import TaskActionProposal
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.task_action import ActionResolution, ActionResponse
from app.services.task_actions import TaskActionError, resolve_proposal

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["task actions"])
Db = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_user)]
Read = Annotated[Workspace, Depends(require_workspace_permission("reviews:read"))]
Resolve = Annotated[Workspace, Depends(require_workspace_permission("reviews:resolve"))]


@router.get("/task-runs/{run_id}/actions", response_model=list[ActionResponse])
def list_actions(run_id: UUID, workspace: Read, db: Db,
                 limit: int = Query(default=20, ge=1, le=100),
                 offset: int = Query(default=0, ge=0)):
    if db.scalar(select(GraphRun.id).where(GraphRun.id == run_id,
                                          GraphRun.workspace_id == workspace.id)) is None:
        raise HTTPException(404, detail="Run not found.")
    rows = db.scalars(select(TaskActionProposal).where(
        TaskActionProposal.workspace_id == workspace.id, TaskActionProposal.graph_run_id == run_id,
    ).order_by(TaskActionProposal.created_at, TaskActionProposal.id).limit(limit).offset(offset))
    return [ActionResponse.from_proposal(row) for row in rows]


@router.post("/task-actions/{proposal_id}/resolve", response_model=ActionResponse)
def resolve_action(proposal_id: UUID, payload: ActionResolution,
                   workspace: Resolve, actor: Actor, db: Db):
    try:
        proposal = resolve_proposal(db, workspace_id=workspace.id, proposal_id=proposal_id,
            reviewer_id=actor.id, expected_hash=payload.expected_hash,
            approve=payload.decision == "approve", reason=payload.reason)
    except TaskActionError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "task_action_conflict",
                                         "message": str(error)}) from error
    return ActionResponse.from_proposal(proposal)
