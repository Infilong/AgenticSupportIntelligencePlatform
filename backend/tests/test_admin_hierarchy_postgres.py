"""Real migration and membership serialization in a disposable PostgreSQL database."""

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from app.services.workspace_service import WorkspaceMemberOwnerError, WorkspaceService


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_role_upgrade_preserves_members_and_concurrent_leaves_keep_an_owner():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "hierarchy_test_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}

    def migrate(revision):
        result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                                env=environment, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr

    try:
        migrate("0032_execution_ownership")
        with Session(target) as db:
            users = [User(email=f"owner{i}@hierarchy.test", display_name="Owner",
                          password_hash="unused") for i in range(3)]
            db.add_all(users)
            db.flush()
            workspace = Workspace(name="Hierarchy migration", created_by_user_id=users[0].id)
            db.add(workspace)
            db.flush()
            ids = [user.id for user in users]
            workspace_id = workspace.id
            for user_id in ids[:2]:
                db.add(WorkspaceMember(workspace_id=workspace_id, user_id=user_id,
                                       role=WorkspaceRole.owner))
            db.add(WorkspaceMember(workspace_id=workspace_id, user_id=ids[2],
                                   role=WorkspaceRole.developer))
            db.commit()
        migrate("0033_admin_operator_roles")
        with Session(target) as db:
            assert db.scalar(select(WorkspaceMember.role).where(
                WorkspaceMember.user_id == ids[2])) == WorkspaceRole.developer
            service = WorkspaceService(db)
            service.update_member_role(workspace_id=workspace_id, user_id=ids[2],
                                       role=WorkspaceRole.admin, actor_user_id=ids[0])
            assert service.get_membership(workspace_id, ids[2]).role == WorkspaceRole.admin
        barrier = Barrier(2)

        def leave(user_id):
            with Session(target) as db:
                # Deliberately preload both memberships to exercise stale ORM state.
                list(db.scalars(select(WorkspaceMember)))
                barrier.wait(timeout=10)
                try:
                    WorkspaceService(db).leave_workspace(workspace_id=workspace_id, user_id=user_id)
                    return "left"
                except WorkspaceMemberOwnerError:
                    db.rollback()
                    return "last_owner"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(leave, ids[:2]))
        assert sorted(results) == ["last_owner", "left"]
        with Session(target) as db:
            owners = list(db.scalars(select(WorkspaceMember).where(
                WorkspaceMember.role == WorkspaceRole.owner)))
            assert len(owners) == 1
            owner_id = owners[0].user_id
        with Session(target) as stale, Session(target) as writer:
            cached = WorkspaceService(stale).get_membership(workspace_id, ids[2])
            assert cached.role == WorkspaceRole.admin
            WorkspaceService(writer).update_member_role(workspace_id=workspace_id,
                user_id=ids[2], role=WorkspaceRole.viewer, actor_user_id=owner_id)
            with pytest.raises(WorkspaceMemberOwnerError):
                WorkspaceService(stale).add_member_by_email(workspace_id=workspace_id,
                    email="missing@hierarchy.test", actor_user_id=ids[2], role=WorkspaceRole.viewer)
            stale.rollback()
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
