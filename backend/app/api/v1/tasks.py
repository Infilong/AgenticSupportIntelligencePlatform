from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.workspace import require_workspace_permission
from app.models.agent import GraphRun
from app.models.task import TaskExecution
from app.models.task_attempt import TaskAttempt
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.agent import GraphRunResponse
from app.schemas.task import TaskCreateRequest, TaskRunResponse
from app.schemas.task_configuration import TaskConfigurationResponse
from app.services.task_admission import TaskAdmissionError, admit_task
from app.services.task_control import TaskControlError, request_stop

router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["tasks"])
Db = Annotated[Session, Depends(get_db)]
Actor = Annotated[User, Depends(get_current_user)]
RunAccess = Annotated[Workspace, Depends(require_workspace_permission("agents:run"))]
ReadAccess = Annotated[Workspace, Depends(require_workspace_permission("traces:read"))]


@router.post("/tasks", response_model=TaskRunResponse, status_code=202)
def create_task(payload: TaskCreateRequest, workspace: RunAccess, actor: Actor, db: Db):
    try:
        task, run = admit_task(db, workspace_id=workspace.id, user_id=actor.id,
            agent_id=payload.agent_id, message=payload.input_message,
            request_key=payload.request_key, language=payload.language)
    except TaskAdmissionError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "task_admission_failed",
                                         "message": str(error)}) from error
    return TaskRunResponse(task_id=task.id, run=GraphRunResponse.model_validate(run))


@router.get("/task-runs/{run_id}", response_model=TaskRunResponse)
def read_task_run(run_id: UUID, workspace: ReadAccess, db: Db):
    run = db.scalar(select(GraphRun).where(GraphRun.id == run_id,
                                           GraphRun.workspace_id == workspace.id))
    if run is None:
        raise HTTPException(404, detail={"code": "run_not_found", "message": "Run not found."})
    execution = db.scalar(select(TaskExecution).where(TaskExecution.graph_run_id == run_id,
                                                      TaskExecution.workspace_id == workspace.id))
    attempt = db.scalar(select(TaskAttempt).where(TaskAttempt.graph_run_id == run_id,
                                                  TaskAttempt.workspace_id == workspace.id))
    return TaskRunResponse(task_id=execution.task_id if execution else None,
                           parent_run_id=attempt.parent_run_id if attempt else None,
                           corrected_instructions=(
                               attempt.corrected_instructions if attempt else None),
                           clarification_reply=attempt.clarification_reply if attempt else None,
                           run=GraphRunResponse.model_validate(run))


@router.post("/task-runs/{run_id}/stop", response_model=GraphRunResponse)
def stop_task_run(run_id: UUID, workspace: RunAccess, actor: Actor, db: Db):
    try:
        run = request_stop(db, workspace_id=workspace.id, run_id=run_id, user_id=actor.id)
    except TaskControlError as error:
        db.rollback()
        raise HTTPException(409, detail={"code": "task_stop_failed",
                                         "message": str(error)}) from error
    return GraphRunResponse.model_validate(run)


@router.get("/task-runs/{run_id}/configuration", response_model=TaskConfigurationResponse)
def read_task_configuration(run_id: UUID, workspace: ReadAccess, db: Db):
    execution = db.scalar(select(TaskExecution).where(TaskExecution.graph_run_id == run_id,
                                                      TaskExecution.workspace_id == workspace.id))
    if execution is None:
        raise HTTPException(404, detail="Saved task configuration not found.")
    try:
        return TaskConfigurationResponse.from_snapshot(execution.agent_snapshot_json)
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(409, detail="Saved task configuration cannot be read.") from error
