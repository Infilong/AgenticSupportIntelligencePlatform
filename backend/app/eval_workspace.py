"""Provision new synthetic evaluation workspaces without altering existing roles or data."""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.engine import make_engine
from app.modules.identity.models import User
from app.modules.workspaces.models import Membership, Workspace


def main():
    settings = Settings()
    if make_url(settings.database_url.get_secret_value()).database != "asi_rebuild":
        raise ValueError("Evaluation provisioning is restricted to the isolated development database")
    engine = make_engine(settings)
    created = {}
    try:
        with Session(engine) as db, db.begin():
            for scope, email in (
                ("primary", "admin@asterworks.example"),
                ("foreign", "private@asterworks.example"),
            ):
                user = db.scalar(select(User).where(User.email == email))
                if user is None:
                    raise ValueError("Provision synthetic demo users first")
                workspace = Workspace(id=uuid.uuid4(), name=f"Evaluation {scope} {uuid.uuid4().hex[:8]}")
                db.add(workspace)
                db.flush()
                db.add(Membership(workspace_id=workspace.id, user_id=user.id, role="admin"))
                created[scope] = str(workspace.id)
        print(json.dumps(created))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
