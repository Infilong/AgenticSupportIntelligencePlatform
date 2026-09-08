"""Upgrade and duplicate submission proof using an isolated PostgreSQL database."""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig, GraphRun
from app.models.task import SupportTask, TaskExecution
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.task_admission import admit_task


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_upgrade_concurrent_admission_and_safe_downgrade_refusal():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "task_admission_" + uuid4().hex
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
        migrate("upgrade", "0033_admin_operator_roles")
        with Session(target) as db:
            user = User(email="task@example.test", display_name="Owner", password_hash="unused")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Task migration", created_by_user_id=user.id)
            db.add(workspace)
            db.flush()
            agent = AgentConfig(workspace_id=workspace.id, name="Support")
            db.add(agent)
            db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id,
                                   role=WorkspaceRole.owner))
            db.commit()
            args = dict(workspace_id=workspace.id, agent_id=agent.id, user_id=user.id,
                        message="退款政策是什么？", request_key="duplicate")
        migrate("upgrade", "0034_support_task_admission")
        migrate("downgrade", "0033_admin_operator_roles")
        migrate("upgrade", "0034_support_task_admission")
        # Verify the historical migration using its own schema, then run current
        # application concurrency behavior against the current schema.
        legacy_id = uuid4()
        with target.begin() as connection:
            connection.execute(text("""INSERT INTO support_tasks
                (id,workspace_id,created_by_user_id,agent_config_id,request_key,request_hash,
                 input_message,created_at) VALUES
                (:id,:workspace,:user,:agent,'historical','historical','Original input',now())"""),
                dict(id=legacy_id, workspace=args["workspace_id"], user=args["user_id"],
                     agent=args["agent_id"]))
        rejected = migrate("downgrade", "0033_admin_operator_roles", success=False)
        assert "Cannot discard persisted support tasks" in rejected.stderr
        with target.begin() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0034_support_task_admission")
            assert connection.scalar(text("SELECT count(*) FROM support_tasks")) == 1
            connection.execute(text("DELETE FROM support_tasks WHERE id=:id"), {"id": legacy_id})
        migrate("upgrade", "head")
        barrier = Barrier(2)

        def submit(_):
            with Session(target) as db:
                barrier.wait(timeout=10)
                task, run = admit_task(db, **args)
                return task.id, run.id

        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(pool.map(submit, range(2)))
        assert ids[0] == ids[1]
        with Session(target) as db:
            for model in (SupportTask, TaskExecution, GraphRun):
                assert db.scalar(select(func.count()).select_from(model)) == 1
            assert db.get(GraphRun, ids[0][1]).status == "queued"
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
