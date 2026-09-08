import json
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from test_task_actions import pending
from test_task_admission import setup

from app.models.agent import AgentConfig, GraphRun
from app.models.task import SupportTask, TaskExecution
from app.models.task_action import TaskNote
from app.models.task_attempt import TaskAttempt
from app.models.workspace import WorkspaceMember
from app.schemas.task_action import TaskActionInput
from app.services.agent_prompt_service import AgentPromptService
from app.services.task_actions import resolve_proposal, stage_proposal
from app.services.task_admission import TaskAdmissionError, admit_task


def test_retry_preserves_parent_and_deduplicates_corrected_attempt(client, db_session):
    args = setup(client)
    task, parent = admit_task(db_session, **args)
    parent.status = "stopped"
    db_session.commit()
    original_settings = db_session.get(AgentConfig, args["agent_id"]).settings_json
    retry = {**args, "request_key": "retry", "parent_run_id": parent.id,
             "corrected_instructions": "Explain the receipt requirement. {literal}"}
    same_task, run = admit_task(db_session, **retry)
    assert same_task.id == task.id
    assert run.id != parent.id
    assert parent.status == "stopped"
    assert db_session.get(TaskAttempt, run.id).parent_run_id == parent.id
    state = json.loads(db_session.get(TaskExecution, run.id).initial_state_json)
    assert state["attempt_instructions"] == retry["corrected_instructions"]
    assert state["task_history"]["previous_attempts"] == [{"run_id": str(parent.id),
                                                           "status": "stopped"}]
    assert "final_answer" not in state["task_history"]
    assert db_session.get(AgentConfig, args["agent_id"]).settings_json == original_settings
    assert admit_task(db_session, **retry)[1].id == run.id
    assert admit_task(db_session, **args)[1].id == parent.id
    with pytest.raises(TaskAdmissionError, match="different request"):
        admit_task(db_session, **{**retry, "corrected_instructions": "Different correction"})
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(SupportTask)) == 1
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == 2
    composed = AgentPromptService(db_session, state)
    assert "receipt requirement" in composed.instructions
    assert str(parent.id) in composed.instructions


@pytest.mark.parametrize("denial", ["active_parent", "foreign", "other_active", "viewer"])
def test_retry_denials_do_not_create_runs(client, db_session, denial):
    args = setup(client)
    _, parent = admit_task(db_session, **args)
    retry = {**args, "request_key": "retry", "parent_run_id": parent.id}
    if denial != "active_parent":
        parent.status = "stopped"
    db_session.commit()
    expected = 1
    if denial == "foreign":
        retry["parent_run_id"] = uuid4()
    elif denial == "other_active":
        admit_task(db_session, **retry)
        retry["request_key"] = "another"
        expected = 2
    elif denial == "viewer":
        member = db_session.scalar(select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == args["workspace_id"]))
        member.role = "viewer"
        db_session.commit()
    with pytest.raises(TaskAdmissionError):
        admit_task(db_session, **retry)
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(GraphRun)) == expected


def test_retried_action_reuses_the_previously_applied_note(client, db_session):
    _, parent, proposal, approval = pending(client, db_session)
    original = resolve_proposal(db_session, **approval)
    parent.status = "completed"
    db_session.commit()
    _, child = admit_task(db_session, workspace_id=parent.workspace_id,
        agent_id=parent.agent_config_id, user_id=parent.user_id, message=parent.input_message,
        request_key="repeat-note", parent_run_id=parent.id)
    child.status = "running"
    repeated = stage_proposal(db_session, run=child,
                               inputs=TaskActionInput.model_validate_json(proposal.inputs_json))
    child.status = "needs_human_review"
    db_session.commit()
    result = resolve_proposal(db_session, **{**approval, "proposal_id": repeated.id,
                                             "expected_hash": repeated.proposal_hash})
    assert json.loads(result.result_json)["reused"] is True
    assert json.loads(result.result_json)["note_id"] == json.loads(original.result_json)["note_id"]
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 1
