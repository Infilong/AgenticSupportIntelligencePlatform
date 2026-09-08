"""One durable execution owner; never automatically replay interrupted model work."""

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun, GraphRunStatus
from app.models.task import TaskExecution
from app.services.execution_ownership import ExecutionBusy, ExecutionOwnershipLost, own_execution
from app.services.graph_outcome import publish_graph_outcome
from app.services.support_agent_graph import SupportAgentGraphRunner
from app.services.task_worker_control import TaskHalt, TaskWorkerControl


def execute_task(engine: Engine, *, workspace_id: UUID, run_id: UUID) -> str:
    with own_execution(engine, workspace_id=workspace_id, execution_id=run_id) as owner:
        with Session(owner.connection) as db:
            control = TaskWorkerControl(db, owner, run_id)
            run = control.locked_run()
            execution = db.get(TaskExecution, run_id)
            if run is None or execution is None or execution.workspace_id != workspace_id:
                raise ValueError("Task execution was not found.")
            if run.status in {GraphRunStatus.running, GraphRunStatus.stopping}:
                # Owning this advisory lock proves there is no surviving database owner.
                # Provider billing may still be uncertain; never replay the graph here.
                return control.terminal("worker_interrupted").status
            if run.status != GraphRunStatus.queued:
                return run.status
            run.status = GraphRunStatus.running
            execution.started_at = datetime.now(UTC)
            initial_state_json = execution.initial_state_json
            db.commit()
            try:
                initial_state = json.loads(initial_state_json)
                state = SupportAgentGraphRunner(db).run(initial_state, before_node=control.check)
                run = control.check("publication", hold=True)
                return publish_graph_outcome(db, run, state).status
            except TaskHalt as error:
                return control.terminal(error.code).status
            except ExecutionOwnershipLost:
                db.rollback()
                raise
            except Exception:
                # Record failure and propagate; do not silently retry model or tool work.
                control.terminal("worker_execution_failed")
                raise


def work_once(engine: Engine) -> bool:
    with Session(engine) as db:
        candidates = list(db.execute(select(GraphRun.workspace_id, GraphRun.id)
            .join(TaskExecution, TaskExecution.graph_run_id == GraphRun.id)
            .where(GraphRun.status.in_(["queued", "running", "stopping"]))
            .order_by(GraphRun.created_at).limit(20)))
    for workspace_id, run_id in candidates:
        try:
            execute_task(engine, workspace_id=workspace_id, run_id=run_id)
            return True
        except ExecutionBusy:
            continue
    return False
