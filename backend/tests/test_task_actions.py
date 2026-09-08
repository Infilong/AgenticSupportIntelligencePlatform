import json
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from test_admin_hierarchy import account
from test_task_admission import setup

from app.models.agent import AgentConfig
from app.models.audit import AuditLog
from app.models.task_action import TaskActionProposal, TaskNote
from app.models.workspace import WorkspaceMember
from app.schemas.task_action import TaskActionInput
from app.services.task_actions import TaskActionError, resolve_proposal, stage_proposal
from app.services.task_admission import admit_task
from app.services.task_control import request_stop


def pending(client, db, action="add_note"):
    args = setup(client)
    agent = db.get(AgentConfig, args["agent_id"])
    agent.settings_json = json.dumps({"allowed_actions": [action]})
    db.commit()
    task, run = admit_task(db, **args)
    run.status = "running"
    proposal = stage_proposal(db, run=run, inputs=TaskActionInput(action=action, value="返金確認"))
    run.status = "needs_human_review"
    db.commit()
    return task, run, proposal, dict(workspace_id=run.workspace_id, proposal_id=proposal.id,
        reviewer_id=args["user_id"], expected_hash=proposal.proposal_hash, approve=True)


@pytest.mark.parametrize("action", ["set_category", "add_note"])
def test_exact_approval_applies_once(client, db_session, action):
    task, _, proposal, args = pending(client, db_session, action)
    assert task.category is None
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0
    for _ in range(2):
        assert resolve_proposal(db_session, **args).status == "applied"
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == (action == "add_note")
    assert task.category == ("返金確認" if action == "set_category" else None)
    assert db_session.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action == "task_action.applied")) == 1
    with pytest.raises(TaskActionError, match="differently"):
        resolve_proposal(db_session, **{**args, "approve": False, "reason": "No"})
    assert proposal.reviewer_id == args["reviewer_id"]


@pytest.mark.parametrize("failure", ["hash", "foreign", "revoked", "agent", "stop", "tamper"])
def test_denial_never_applies_action(client, db_session, failure):
    _, run, proposal, args = pending(client, db_session)
    if failure == "hash":
        args["expected_hash"] = "old-proposal"
    elif failure == "foreign":
        args["proposal_id"] = uuid4()
    elif failure == "revoked":
        member = db_session.scalar(select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == run.workspace_id))
        member.role = "viewer"
    elif failure == "agent":
        db_session.get(AgentConfig, run.agent_config_id).settings_json = "{}"
    elif failure == "tamper":
        proposal.inputs_json = TaskActionInput(
            action="add_note", value="Different inputs").canonical()
    else:
        request_stop(db_session, workspace_id=run.workspace_id, run_id=run.id,
                     user_id=args["reviewer_id"])
    db_session.commit()
    with pytest.raises(TaskActionError):
        resolve_proposal(db_session, **args)
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0
    assert db_session.get(TaskActionProposal, proposal.id).status == (
        "rejected" if failure == "stop" else "pending")


def test_rejection_and_failed_commit_do_not_mutate_task(client, db_session, monkeypatch):
    _, _, proposal, args = pending(client, db_session)
    commit = db_session.commit

    def fail():
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(db_session, "commit", fail)
    with pytest.raises(RuntimeError, match="storage unavailable"):
        resolve_proposal(db_session, **args)
    monkeypatch.setattr(db_session, "commit", commit)
    assert db_session.get(TaskActionProposal, proposal.id).status == "pending"
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0
    assert resolve_proposal(db_session, **{**args, "approve": False,
        "reason": "Insufficient evidence"}).status == "rejected"
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0


def test_action_requires_explicit_snapshot_capability(client, db_session):
    args = setup(client)
    _, run = admit_task(db_session, **args)
    run.status = "running"
    db_session.get(AgentConfig, args["agent_id"]).settings_json = '{"allowed_actions":["add_note"]}'
    with pytest.raises(TaskActionError):
        stage_proposal(db_session, run=run, inputs=TaskActionInput(action="add_note", value="Note"))


def test_separate_reviewer_cannot_restore_revoked_initiator_authority(client, db_session):
    _, run, _, args = pending(client, db_session)
    user, _, _ = account(client, "separate-reviewer")
    db_session.add(WorkspaceMember(workspace_id=run.workspace_id, user_id=UUID(user), role="owner"))
    initiator = db_session.scalar(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == run.workspace_id, WorkspaceMember.user_id == run.user_id))
    initiator.role = "viewer"
    db_session.commit()
    with pytest.raises(TaskActionError, match="initiating user"):
        resolve_proposal(db_session, **{**args, "reviewer_id": UUID(user)})
    db_session.rollback()
    assert db_session.scalar(select(func.count()).select_from(TaskNote)) == 0
