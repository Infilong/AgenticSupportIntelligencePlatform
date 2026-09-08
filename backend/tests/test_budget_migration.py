"""Upgrade/rollback the new migration in a disposable database, never the application DB."""

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_reservation_migration_upgrade_downgrade_upgrade():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "budget_migration_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}
    try:
        for command, revision, expected in [
            ("upgrade", "head", True), ("downgrade", "0025_ai_run_prompt_hash", False),
            ("upgrade", "head", True),
        ]:
            result = subprocess.run(["alembic", command, revision], env=environment,
                                    capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, result.stderr
            assert inspect(target).has_table("model_call_reservations") is expected
        constraints = inspect(target).get_check_constraints("model_call_reservations")
        assert {item["name"] for item in constraints} == {
            "ck_reservation_tokens", "ck_reservation_cost", "ck_reservation_status",
            "ck_reservation_context"}
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
