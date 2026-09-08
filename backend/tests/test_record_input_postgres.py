"""Upgrade legacy inputs, persist structured originals and refuse lossy downgrade."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig, GraphRun
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.record_input import RecordInput
from app.services.record_queries import list_records, read_record
from app.services.task_admission import admit_task


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_record_input_upgrade_and_downgrade_preserve_originals():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "record_input_" + uuid4().hex
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
        migrate("upgrade", "0037_retire_legacy_roles")
        with Session(target) as db:
            user = User(email="records@example.test", display_name="Owner", password_hash="unused")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Records migration", created_by_user_id=user.id)
            db.add(workspace)
            db.flush()
            agent = AgentConfig(workspace_id=workspace.id, name="Processor")
            db.add(agent)
            db.flush()
            db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner"))
            args = dict(workspace_id=workspace.id, agent_id=agent.id, user_id=user.id)
            legacy_id = uuid4()
            db.execute(text("""INSERT INTO support_tasks
                (id,workspace_id,created_by_user_id,agent_config_id,request_key,request_hash,
                 input_message,created_at) VALUES
                (:id,:workspace,:user,:agent,'legacy','legacy','Original legacy text',now())"""),
                dict(id=legacy_id, workspace=workspace.id, user=user.id, agent=agent.id))
            db.commit()
        migrate("upgrade", "0038_record_original_input")
        # No metadata exists yet: an additive migration can round-trip without data loss.
        migrate("downgrade", "0037_retire_legacy_roles")
        migrate("upgrade", "0038_record_original_input")
        with Session(target) as db:
            legacy = db.execute(text("SELECT input_message,input_envelope_json FROM support_tasks "
                                     "WHERE id=:id"), {"id": legacy_id}).one()
            assert legacy == ("Original legacy text", None)
            original = RecordInput(format="json", content={"question": "Refund?", "days": 3})
            task, run = admit_task(db, **args, message=original.processing_text(),
                                  request_key="original", record_input=original)
            detail = read_record(db, workspace_id=args["workspace_id"], record_id=task.id)
            assert detail.input == original
            assert detail.latest_run_id == run.id
            assert list_records(db, workspace_id=args["workspace_id"], status="queued").total == 1
        rejected = migrate("downgrade", "0037_retire_legacy_roles", success=False)
        assert "Cannot discard original record data" in rejected.stderr
        with Session(target) as db:
            assert read_record(db, workspace_id=args["workspace_id"], record_id=task.id).input == (
                original)
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0038_record_original_input")
        migrate("upgrade", "0039_record_clarification")
        migrate("downgrade", "0038_record_original_input")
        migrate("upgrade", "0039_record_clarification")
        with Session(target) as db:
            parent = db.get(GraphRun, detail.latest_run_id)
            parent.status = "awaiting_clarification"
            parent.final_answer = "Which purchase?"
            db.commit()
            _, child = admit_task(db, **args, message="Purchase 42", request_key="clarified",
                parent_run_id=parent.id, clarification_reply="Purchase 42")
            child_id = child.id
        refused = migrate("downgrade", "0038_record_original_input", success=False)
        assert "Cannot discard clarification replies" in refused.stderr
        with Session(target) as db:
            assert db.scalar(text("SELECT clarification_reply FROM task_attempts "
                                  "WHERE graph_run_id=:id"), {"id": child_id}) == "Purchase 42"
            assert read_record(db, workspace_id=args["workspace_id"], record_id=task.id).input == (
                original)
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
