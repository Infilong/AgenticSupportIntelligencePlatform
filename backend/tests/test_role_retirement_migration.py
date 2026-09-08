import json
import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_legacy_roles_migrate_with_audit_and_cannot_be_reintroduced():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "role_retirement_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as db:
        db.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {
        **os.environ,
        "DATABASE_URL": url.set(database=name).render_as_string(hide_password=False),
    }

    def migrate(command, revision):
        return subprocess.run(
            [sys.executable, "-m", "alembic", command, revision],
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )

    try:
        before = migrate("upgrade", "0036_task_attempts")
        assert before.returncode == 0, before.stderr
        workspace, owner = uuid4(), uuid4()
        roles = ["owner", "viewer", "reviewer", "member", "developer"]
        with target.begin() as db:
            for role in roles:
                user = owner if role == "owner" else uuid4()
                db.execute(
                    text(
                        "INSERT INTO users (id,email,display_name,password_hash,created_at) "
                        "VALUES (:id,:email,:name,'unused',now())"
                    ),
                    {"id": user, "email": role + "@retirement.test", "name": role},
                )
                if role == "owner":
                    db.execute(
                        text(
                            "INSERT INTO workspaces (id,name,created_by_user_id,created_at) "
                            "VALUES (:id,'Retirement',:owner,now())"
                        ),
                        {"id": workspace, "owner": owner},
                    )
                db.execute(
                    text(
                        "INSERT INTO workspace_members (id,workspace_id,user_id,role,created_at) "
                        "VALUES (:id,:workspace,:user,CAST(:role AS workspacerole),now())"
                    ),
                    {"id": uuid4(), "workspace": workspace, "user": user, "role": role},
                )
        result = migrate("upgrade", "head")
        assert result.returncode == 0, result.stderr
        with target.connect() as db:
            assert sorted(db.scalars(text("SELECT role::text FROM workspace_members"))) == [
                "admin",
                "admin",
                "operator",
                "owner",
                "viewer",
            ]
            assert db.scalar(text("SELECT count(*) FROM users")) == 5
            assert db.scalar(text("SELECT count(*) FROM workspaces")) == 1
            history = [
                json.loads(row)
                for row in db.scalars(
                    text(
                        "SELECT metadata_json FROM audit_logs "
                        "WHERE action='workspace.role_migrated'"
                    )
                )
            ]
            assert {(row["previous_role"], row["new_role"]) for row in history} == {
                ("reviewer", "operator"),
                ("member", "admin"),
                ("developer", "admin"),
            }
        with pytest.raises(IntegrityError), target.begin() as db:
            db.execute(
                text("UPDATE workspace_members SET role='reviewer' WHERE user_id=:owner"),
                {"owner": owner},
            )
        assert migrate("downgrade", "0036_task_attempts").returncode != 0
        with target.connect() as db:
            assert (
                db.scalar(text("SELECT version_num FROM alembic_version"))
                == "0037_retire_legacy_roles"
            )
    finally:
        target.dispose()
        with admin.connect() as db:
            db.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
