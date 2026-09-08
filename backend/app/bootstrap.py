"""Explicit synthetic-account provisioning for the isolated development database only."""

import os
import uuid

from sqlalchemy import select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.engine import make_engine
from app.modules.identity.models import User
from app.modules.identity.security import passwords
from app.modules.workspaces.models import Membership, Workspace

ACCOUNTS = {
    "admin": "admin@asterworks.example",
    "operator": "operator@asterworks.example",
    "viewer": "viewer@asterworks.example",
    "private": "private@asterworks.example",
}


def seed(settings, password):
    if make_url(settings.database_url.get_secret_value()).database != "asi_rebuild" or len(password) < 20:
        raise ValueError(
            "Demo provisioning requires the isolated asi_rebuild database and a generated password"
        )
    engine = make_engine(settings)
    try:
        with Session(engine) as db:
            db.execute(text("SELECT pg_advisory_xact_lock(73192001)"))
            primary_id = uuid.uuid5(uuid.NAMESPACE_URL, "asi-rebuild-v1:demo-primary")
            private_id = uuid.uuid5(uuid.NAMESPACE_URL, "asi-rebuild-v1:demo-private")
            for workspace_id, name in ((primary_id, "AsterWorks Support"), (private_id, "Private Sandbox")):
                if db.get(Workspace, workspace_id) is None:
                    db.add(Workspace(id=workspace_id, name=name))
            db.flush()
            for role, email in ACCOUNTS.items():
                user = db.scalar(select(User).where(User.email == email))
                created = user is None
                if user is None:
                    user = User(
                        email=email,
                        display_name=f"Demo {role.title()}",
                        password_hash=passwords.hash(password),
                    )
                    db.add(user)
                    db.flush()
                elif not passwords.verify(password, user.password_hash):
                    raise ValueError(
                        "Existing demo account credentials differ; no passwords or memberships changed"
                    )
                workspace_id = private_id if role == "private" else primary_id
                if created:
                    db.add(
                        Membership(
                            workspace_id=workspace_id,
                            user_id=user.id,
                            role="admin" if role == "private" else role,
                        )
                    )
            db.commit()
    finally:
        engine.dispose()


if __name__ == "__main__":
    seed(Settings(), os.environ["ASI_DEMO_PASSWORD"])
    print("Synthetic development accounts provisioned; no credentials printed.")
