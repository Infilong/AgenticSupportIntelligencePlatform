"""Retry admission and bounded history use the same task authority as the browser."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.v1.tasks import Actor, Db, ReadAccess, RunAccess
from app.models.agent import GraphRun
from app.models.task import TaskExecution
from app.models.task_attempt import TaskAttempt
from app.schemas.agent import GraphRunResponse
from app.schemas.task import TaskAttemptPage, TaskRetryRequest, TaskRunResponse
from app.services.task_admission import TaskAdmissionError, admit_task

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["tasks"])


@router.post("/task-runs/{run_id}/retry", response_model=TaskRunResponse, status_code=202)
def retry_task(run_id: UUID, payload: TaskRetryRequest, workspace: RunAccess, actor: Actor, db: Db):
    parent = db.scalar(select(GraphRun).where(GraphRun.id == run_id,
                                               GraphRun.workspace_id == workspace.id))
    if parent is None:
        raise HTTPException(404, detail="Task run not found.")
    if not payload.corrected_instructions.strip():
        raise HTTPException(422, detail="Corrected instructions must not be blank.")
    try:
        task, run = admit_task(db, workspace_id=workspace.id, user_id=actor.id,
            agent_id=parent.agent_config_id, message=parent.input_message,
            language=parent.language, request_key=payload.request_key, parent_run_id=run_id,
            corrected_instructions=payload.corrected_instructions)
    except TaskAdmissionError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "task_retry_failed",
                                         "message": str(error)}) from error
    return TaskRunResponse(task_id=task.id, run=GraphRunResponse.model_validate(run),
        parent_run_id=run_id, corrected_instructions=payload.corrected_instructions.strip())


@router.get("/task-runs/{run_id}/attempts", response_model=TaskAttemptPage)
def list_attempts(run_id: UUID, workspace: ReadAccess, db: Db,
                  limit: int = Query(default=20, ge=1, le=100),
                  offset: int = Query(default=0, ge=0)):
    execution = db.scalar(select(TaskExecution).where(TaskExecution.graph_run_id == run_id,
                                                      TaskExecution.workspace_id == workspace.id))
    if execution is None:
        raise HTTPException(404, detail="Task run not found.")
    filters = (TaskExecution.task_id == execution.task_id,
               TaskExecution.workspace_id == workspace.id, GraphRun.workspace_id == workspace.id)
    total = db.scalar(select(func.count()).select_from(TaskExecution)
        .join(GraphRun, GraphRun.id == TaskExecution.graph_run_id).where(*filters)) or 0
    rows = db.execute(select(GraphRun, TaskAttempt).join(TaskExecution,
        TaskExecution.graph_run_id == GraphRun.id).outerjoin(TaskAttempt,
        (TaskAttempt.graph_run_id == GraphRun.id) & (TaskAttempt.workspace_id == workspace.id))
        .where(*filters).order_by(GraphRun.created_at.desc(), GraphRun.id)
        .limit(limit).offset(offset))
    return TaskAttemptPage(items=[TaskRunResponse(task_id=execution.task_id,
        run=GraphRunResponse.model_validate(run),
        parent_run_id=attempt.parent_run_id if attempt else None,
        corrected_instructions=attempt.corrected_instructions if attempt else None,
        clarification_reply=attempt.clarification_reply if attempt else None)
        for run, attempt in rows], total=total, has_next=offset + limit < total)
