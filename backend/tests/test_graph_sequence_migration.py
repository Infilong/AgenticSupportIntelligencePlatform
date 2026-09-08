"""Upgrade legacy history without guessing order; block destructive rollback."""

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig, GraphRun
from app.models.user import User
from app.models.workspace import Workspace


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_graph_sequence_upgrade_preserves_unknown_history_and_guards_rollback():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "graph_migration_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}

    def migrate(command, revision, success=True):
        result = subprocess.run(["alembic", command, revision], env=environment,
                                capture_output=True, text=True, timeout=60)
        assert (result.returncode == 0) is success, result.stderr
        return result

    try:
        migrate("upgrade", "0030_evaluation_reservations")
        with Session(target) as db:
            user = User(email="migration@example.test", password_hash="unused", display_name="Test")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Migration", created_by_user_id=user.id)
            db.add(workspace)
            db.flush()
            agent = AgentConfig(workspace_id=workspace.id, name="Migration")
            db.add(agent)
            db.flush()
            run = GraphRun(workspace_id=workspace.id, agent_config_id=agent.id, user_id=user.id,
                           input_message="Refund?", language="en", status="running")
            db.add(run)
            db.flush()
            ids = dict(id=uuid4(), workspace=workspace.id, run=run.id)
            db.execute(text("INSERT INTO graph_steps (id, workspace_id, graph_run_id, "
                "step_name, input_json, output_json, status, latency_ms, retry_count, created_at) "
                "VALUES (:id, :workspace, :run, 'legacy', '{}', '{}', 'succeeded', 1, 0, now())"),
                ids)
            db.commit()
        migrate("upgrade", "head")
        assert any(item["column_names"] == ["graph_run_id", "sequence"]
                   for item in inspect(target).get_unique_constraints("graph_steps"))
        with target.connect() as connection:
            assert connection.execute(text(
                "SELECT step_name, sequence FROM graph_steps WHERE id=:id"), ids).one() == (
                    "legacy", None)
        migrate("downgrade", "0030_evaluation_reservations")
        migrate("upgrade", "head")
        with target.begin() as connection:
            connection.execute(text("UPDATE graph_steps SET sequence=1 WHERE id=:id"), ids)
        with pytest.raises(IntegrityError), target.begin() as connection:
            connection.execute(text("UPDATE graph_steps SET sequence=0 WHERE id=:id"), ids)
        rejected = migrate("downgrade", "0030_evaluation_reservations", success=False)
        assert "sequenced graph history exists" in rejected.stderr
        with target.connect() as connection:
            sequence = connection.scalar(text("SELECT sequence FROM graph_steps WHERE id=:id"), ids)
            assert sequence == 1
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0032_execution_ownership")
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
