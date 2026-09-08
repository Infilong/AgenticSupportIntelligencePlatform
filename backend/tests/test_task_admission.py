import json
from uuid import UUID

import pytest
from sqlalchemy import event, func, select
from test_admin_hierarchy import account

from app.models.agent import AgentConfig, GraphRun
from app.models.task import SupportTask, TaskExecution
from app.services.task_admission import TaskAdmissionError, admit_task


def setup(client):
    user, _, headers = account(client, "task-owner")
    workspace = client.post("/api/v1/workspaces", headers=headers,
                            json={"name": "Tasks"}).json()["id"]
    agent = client.post(f"/api/v1/workspaces/{workspace}/agents", headers=headers,
                        json={"name": "Support"}).json()["id"]
    return {"workspace_id": UUID(workspace), "agent_id": UUID(agent), "user_id": UUID(user),
            "message": "返金ポリシーを教えてください", "request_key": "same-request"}


def test_admission_snapshots_and_idempotency(client, db_session):
    args = setup(client)
    agent = db_session.get(AgentConfig, args["agent_id"])
    agent.settings_json = json.dumps({"instructions": "Keep replies concise."})
    db_session.commit()
    task, run = admit_task(db_session, **args)
    assert run.status == "queued"
    execution = db_session.get(TaskExecution, run.id)
    assert execution.task_id == task.id
    state = json.loads(execution.initial_state_json)
    assert state["input_message"] == args["message"]
    assert state["agent_settings"]["instructions"] == "Keep replies concise."
    agent.settings_json = "{}"
    db_session.commit()
    same_task, same_run = admit_task(db_session, **args)
    assert (same_task.id, same_run.id) == (task.id, run.id)
    assert json.loads(execution.agent_snapshot_json)["settings"]["instructions"]
    with pytest.raises(TaskAdmissionError, match="different request"):
        admit_task(db_session, **{**args, "message": "Different input"})
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == 1


def test_admission_denies_foreign_user_and_agent(client, db_session):
    args = setup(client)
    outsider, _, headers = account(client, "outsider")
    with pytest.raises(TaskAdmissionError, match="permission"):
        admit_task(db_session, **{**args, "user_id": UUID(outsider)})
    db_session.rollback()
    other_workspace = client.post("/api/v1/workspaces", headers=headers,
                                  json={"name": "Foreign"}).json()["id"]
    foreign_agent = client.post(f"/api/v1/workspaces/{other_workspace}/agents", headers=headers,
                                json={"name": "Other agent"}).json()["id"]
    with pytest.raises(TaskAdmissionError, match="available workspace agent"):
        admit_task(db_session, **{**args, "agent_id": UUID(foreign_agent)})
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 0
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == 0


def test_failed_admission_does_not_leave_partial_task_or_run(client, db_session):
    args = setup(client)

    def fail_execution(session, context, instances):
        if any(isinstance(item, TaskExecution) for item in session.new):
            raise RuntimeError("synthetic admission failure")

    event.listen(db_session, "before_flush", fail_execution)
    try:
        with pytest.raises(RuntimeError, match="synthetic admission failure"):
            admit_task(db_session, **args)
        db_session.rollback()
    finally:
        event.remove(db_session, "before_flush", fail_execution)
    for model in (SupportTask, GraphRun, TaskExecution):
        assert db_session.scalar(select(func.count()).select_from(model)) == 0
