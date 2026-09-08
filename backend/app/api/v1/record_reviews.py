"""Locate a review for one authorized record attempt."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.v1.records import Db
from app.dependencies.workspace import require_workspace_permission
from app.models.agent import GraphRun
from app.models.review import HumanReview
from app.models.task import SupportTask, TaskExecution
from app.models.workspace import Workspace
from app.schemas.human_review import HumanReviewResponse

router = APIRouter(prefix="/workspaces/{workspace_id}/records", tags=["records"])
Access = Annotated[Workspace, Depends(require_workspace_permission("reviews:read"))]


@router.get("/{record_id}/attempts/{run_id}/review", response_model=HumanReviewResponse | None)
def review(record_id: UUID, run_id: UUID, workspace: Access, db: Db):
    owned = db.scalar(select(GraphRun.id).join(TaskExecution,
        TaskExecution.graph_run_id == GraphRun.id).join(SupportTask,
        SupportTask.id == TaskExecution.task_id).where(
        GraphRun.id == run_id, GraphRun.workspace_id == workspace.id,
        TaskExecution.workspace_id == workspace.id, SupportTask.workspace_id == workspace.id,
        SupportTask.id == record_id))
    if owned is None:
        raise HTTPException(404, detail="Record attempt not found.")
    return db.scalar(select(HumanReview).where(HumanReview.workspace_id == workspace.id,
        HumanReview.graph_run_id == run_id).order_by(HumanReview.created_at.desc(),
                                                    HumanReview.id.desc()).limit(1))
