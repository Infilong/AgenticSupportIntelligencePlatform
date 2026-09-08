import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.main import create_app
from app.modules.identity.models import User
from app.modules.identity.security import passwords
from app.modules.workspaces.models import Membership, Workspace

PASSWORD = "Synthetic-test-password-42"
ORIGIN = "http://127.0.0.1:5180"


@pytest.fixture
def system():
    url = os.environ.get("ASI_TEST_DATABASE_URL")
    if not url or make_url(url).database != "asi_rebuild_test":
        pytest.fail(
            "Use scripts/verify_integration.py; tests require the dedicated asi_rebuild_test database"
        )
    base = create_engine(url, hide_parameters=True)
    schema = "test_" + uuid.uuid4().hex
    with base.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped = make_url(url).update_query_dict({"options": f"-c search_path={schema},public"})
    engine = create_engine(scoped, hide_parameters=True)
    try:
        with engine.begin() as connection:
            config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        settings = Settings(database_url=scoped.render_as_string(hide_password=False))
        app = create_app(settings)
        with Session(engine, expire_on_commit=False) as db:
            users = {}
            for role in ("admin", "operator", "viewer", "other"):
                user = User(
                    email=f"{role}@example.test", display_name=role, password_hash=passwords.hash(PASSWORD)
                )
                db.add(user)
                users[role] = user
            workspace = Workspace(name="Primary")
            foreign = Workspace(name="Foreign")
            db.add_all([workspace, foreign])
            db.flush()
            for role in ("admin", "operator", "viewer"):
                db.add(Membership(workspace_id=workspace.id, user_id=users[role].id, role=role))
            db.add(Membership(workspace_id=foreign.id, user_id=users["other"].id, role="admin"))
            db.commit()
        with TestClient(app) as client:
            # Preserve test schema while using the exact application engine factory and endpoints.
            yield {
                "client": client,
                "engine": engine,
                "users": users,
                "workspace": workspace.id,
                "foreign": foreign.id,
                "app": app,
            }
    finally:
        engine.dispose()
        with base.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        base.dispose()


def login(client, role="admin"):
    csrf = client.get("/api/session").json()["csrf_token"]
    response = client.post(
        "/api/session/login",
        json={"email": f"{role}@example.test", "password": PASSWORD},
        headers={"Origin": ORIGIN, "X-CSRF-Token": csrf},
    )
    assert response.status_code == 200, response.text
    return {"Origin": ORIGIN, "X-CSRF-Token": response.json()["csrf_token"]}
