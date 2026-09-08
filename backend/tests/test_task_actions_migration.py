"""Alembic upgrade preservation and refusal to discard action history."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig
from app.models.task_action import TaskNote
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.task_action import TaskActionInput
from app.services.task_actions import resolve_proposal, stage_proposal
from app.services.task_admission import admit_task


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_action_migration_preserves_tasks_and_refuses_history_loss():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "task_actions_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}

    def migrate(command, revision, success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", command, revision],
                                env=environment, capture_output=True, text=True, timeout=60)
        assert (result.returncode == 0) is success, result.stderr
        return result

    try:
        migrate("upgrade", "0034_support_task_admission")
        with Session(target) as db:
            user = User(email="actions@example.test", display_name="Owner", password_hash="unused")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Actions", created_by_user_id=user.id)
            db.add(workspace)
            db.flush()
            agent = AgentConfig(workspace_id=workspace.id, name="Support",
                                settings_json='{"allowed_actions":["add_note"]}')
            db.add(agent)
            db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
            db.commit()
            task, run = admit_task(db, workspace_id=workspace.id, agent_id=agent.id,
                user_id=user.id, message="返金について", request_key="migration")
            task_id, run_id, workspace_id, user_id = task.id, run.id, workspace.id, user.id
        migrate("upgrade", "0035_task_actions")
        migrate("downgrade", "0034_support_task_admission")
        migrate("upgrade", "0035_task_actions")
        with target.connect() as connection:
            assert connection.scalar(text("SELECT input_message FROM support_tasks WHERE id=:id"),
                                     {"id": task_id}) == "返金について"
        from app.models.agent import GraphRun
        with Session(target) as db:
            run = db.get(GraphRun, run_id)
            run.status = "running"
            proposal = stage_proposal(db, run=run, inputs=TaskActionInput(
                action="add_note", value="確認済み"))
            run.status = "needs_human_review"
            db.commit()
            result = resolve_proposal(db, workspace_id=workspace_id, proposal_id=proposal.id,
                reviewer_id=user_id, expected_hash=proposal.proposal_hash, approve=True)
            saved_hash = result.proposal_hash
            assert db.query(TaskNote).one().content == "確認済み"
        refused = migrate("downgrade", "0034_support_task_admission", success=False)
        assert "Cannot discard task action history" in refused.stderr
        with target.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0035_task_actions")
            assert connection.scalar(text("SELECT proposal_hash FROM task_action_proposals")) == (
                saved_hash)
            assert connection.scalar(text("SELECT content FROM task_notes")) == "確認済み"
        migrate("upgrade", "0036_task_attempts")
        migrate("downgrade", "0035_task_actions")
        migrate("upgrade", "0036_task_attempts")
        with Session(target) as db:
            parent = db.get(GraphRun, run_id)
            parent.status = "completed"
            db.commit()
            _, retry = admit_task(db, workspace_id=workspace_id, agent_id=parent.agent_config_id,
                user_id=user_id, message=parent.input_message, request_key="retry",
                parent_run_id=run_id, corrected_instructions="領収書について説明してください")
            assert retry.id != run_id
            assert db.query(TaskNote).one().content == "確認済み"
        refused = migrate("downgrade", "0035_task_actions", success=False)
        assert "Cannot discard linked task attempt history" in refused.stderr
        with target.connect() as connection:
            assert connection.scalar(text("SELECT parent_run_id FROM task_attempts")) == run_id
            assert connection.scalar(text("SELECT corrected_instructions FROM task_attempts")) == (
                "領収書について説明してください")
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
