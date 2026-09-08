"""Worker checks and durable terminal state on the execution owner's connection."""

import json
from datetime import UTC, datetime

from sqlalchemy import select

from app.models.agent import AgentConfig, Checkpoint, GraphRun, GraphRunStatus
from app.models.task import TaskExecution
from app.models.workspace import Workspace, WorkspaceMember
from app.services.workspace_service import permissions_for_role


class TaskHalt(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class TaskWorkerControl:
    def __init__(self, db, owner, run_id):
        self.db, self.owner, self.run_id = db, owner, run_id
        self.steps = 0

    def locked_run(self):
        self.db.commit()
        self.owner.assert_owned()
        self.owner.connection.commit()
        return self.db.scalar(select(GraphRun).where(
            GraphRun.id == self.run_id, GraphRun.workspace_id == self.owner.workspace_id,
        ).with_for_update().execution_options(populate_existing=True))

    def check(self, name, *, hold=False):
        run = self.locked_run()
        execution = self.db.get(TaskExecution, self.run_id, populate_existing=True)
        if run.status in {GraphRunStatus.stopping, GraphRunStatus.stopped}:
            raise TaskHalt("stopped")
        if run.status != GraphRunStatus.running:
            raise TaskHalt("invalid_execution_state")
        workspace = self.db.get(Workspace, run.workspace_id, populate_existing=True)
        member = self.db.scalar(select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == run.workspace_id,
            WorkspaceMember.user_id == run.user_id,
        ).execution_options(populate_existing=True))
        agent = self.db.get(AgentConfig, run.agent_config_id, populate_existing=True)
        if (workspace.deleted_at or workspace.archived_at or member is None
                or "agents:run" not in permissions_for_role(member.role)
                or agent is None or not agent.active or agent.archived_at):
            raise TaskHalt("execution_permission_revoked")
        started = execution.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=UTC)
        if (datetime.now(UTC) - started).total_seconds() >= execution.max_seconds:
            raise TaskHalt("execution_time_limit")
        if name != "publication":
            self.steps += 1
            if self.steps > execution.max_steps:
                raise TaskHalt("execution_step_limit")
        if not hold:
            self.db.commit()
        return run

    def terminal(self, code):
        self.db.rollback()
        run = self.locked_run()
        execution = self.db.get(TaskExecution, self.run_id, populate_existing=True)
        if run.status in {GraphRunStatus.completed, GraphRunStatus.needs_human_review,
                          GraphRunStatus.rejected, GraphRunStatus.stopped,
                          GraphRunStatus.awaiting_clarification}:
            return run
        stopped = code == "stopped" or run.status == GraphRunStatus.stopping
        run.status = GraphRunStatus.stopped if stopped else GraphRunStatus.failed
        run.route_decision = "stopped" if stopped else code
        run.completed_at = datetime.now(UTC)
        run.final_answer = None
        execution.error_code = None if stopped else code
        self.db.add(Checkpoint(workspace_id=run.workspace_id, graph_run_id=run.id,
            checkpoint_key="worker_stopped" if stopped else "worker_failed",
            state_json=json.dumps({"status": run.status, "error_code": execution.error_code})))
        self.db.commit()
        return run
