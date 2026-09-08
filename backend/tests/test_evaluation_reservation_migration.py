import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent import AgentConfig, GraphRun
from app.models.evaluation import EvaluationRun
from app.models.user import User
from app.models.workspace import Workspace


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_evaluation_reservation_upgrade_and_lossless_rollback():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "evaluation_migration_" + uuid4().hex
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
        migrate("upgrade", "0029_retrieval_outcome")
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
            graph = GraphRun(workspace_id=workspace.id, agent_config_id=agent.id, user_id=user.id,
                             input_message="Refund?", language="en", status="running")
            evaluation = EvaluationRun(workspace_id=workspace.id, name="Migration",
                created_by_user_id=user.id, modes_json='["direct_llm"]',
                status="running", total_cases=1)
            db.add_all([graph, evaluation])
            db.flush()
            ids = dict(id=uuid4(), workspace=workspace.id, graph=graph.id, evaluation=evaluation.id)
            db.execute(text("INSERT INTO model_call_reservations "
                "(id, workspace_id, graph_run_id, purpose, estimated_tokens, estimated_cost, "
                "status, expires_at, created_at) VALUES "
                "(:id, :workspace, :graph, 'draft_response', 100, 0.001, 'reserved', "
                "now() + interval '1 hour', now())"), ids)
            db.commit()
        migrate("upgrade", "head")
        with target.begin() as connection:
            old = connection.execute(text(
                "SELECT graph_run_id, evaluation_run_id, estimated_tokens "
                "FROM model_call_reservations WHERE id=:id"), ids).one()
            assert old == (ids["graph"], None, 100)
        migrate("downgrade", "0029_retrieval_outcome")
        migrate("upgrade", "head")
        with target.begin() as connection:
            connection.execute(text("INSERT INTO model_call_reservations "
                "(id, workspace_id, evaluation_run_id, purpose, estimated_tokens, estimated_cost, "
                "status, expires_at, created_at) VALUES "
                "(:new_id, :workspace, :evaluation, 'evaluation_direct_llm', "
                "100, 0.001, 'consumed', "
                "now(), now())"), {**ids, "new_id": uuid4()})
        rejected = migrate("downgrade", "0029_retrieval_outcome", success=False)
        assert "while evaluation reservations exist" in rejected.stderr
        with target.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM model_call_reservations")) == 2
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0032_execution_ownership")
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
