import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.models.workspace import Workspace


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_ownership_migration_preserves_legacy_and_guards_history():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "ownership_migration_" + uuid4().hex
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
        migrate("upgrade", "0031_graph_step_sequence")
        with Session(target) as db:
            user = User(email="ownership@example.test", password_hash="unused", display_name="Test")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Migration", created_by_user_id=user.id)
            db.add(workspace)
            db.flush()
            values = {"id": uuid4(), "workspace": workspace.id}
            db.execute(text("INSERT INTO ai_runs (id, workspace_id, provider, model, purpose, "
                "language, prompt_tokens, completion_tokens, total_tokens, estimated_cost, "
                "latency_ms, cache_hit, status, created_at) VALUES (:id, :workspace, 'openai', "
                "'text-embedding-3-small', 'embedding_query', 'en', 12, 0, 12, 0.001, 0, "
                "false, 'pending', now())"), values)
            db.commit()
        migrate("upgrade", "0032_execution_ownership")
        with target.connect() as connection:
            assert connection.execute(text("SELECT execution_id, execution_protocol, total_tokens "
                "FROM ai_runs WHERE id=:id"), values).one() == (None, None, 12)
        migrate("downgrade", "0031_graph_step_sequence")
        migrate("upgrade", "0032_execution_ownership")
        for assignment in ("execution_id = gen_random_uuid()",
                           "execution_protocol = 'pg-session-v1'",
                           "execution_id = gen_random_uuid(), execution_protocol = 'unknown'"):
            with pytest.raises(IntegrityError), target.begin() as connection:
                connection.execute(text(f"UPDATE ai_runs SET {assignment} WHERE id=:id"), values)
        with target.begin() as connection:
            connection.execute(text("UPDATE ai_runs SET execution_id=gen_random_uuid(), "
                "execution_protocol='pg-session-v1' WHERE id=:id"), values)
        rejected = migrate("downgrade", "0031_graph_step_sequence", success=False)
        assert "execution ownership history exists" in rejected.stderr
        with target.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0032_execution_ownership")
            assert connection.scalar(text("SELECT execution_protocol FROM ai_runs WHERE id=:id"),
                                     values) == "pg-session-v1"
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
