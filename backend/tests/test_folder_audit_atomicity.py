import os

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_resource_folders import auth_headers, create_folder, create_workspace, login, register
from test_review_transactions import review_database as review_database

from app.models.audit import AuditLog
from app.models.folder import ResourceFolder
from app.models.user import User
from app.services.folder_service import ResourceFolderService


@pytest.mark.parametrize("operation", ["create", "rename", "delete"])
def test_audit_failure_rolls_back_folder_and_allows_retry(client, db_session, operation):
    register(client, "folder-atomic@example.test")
    token = login(client, "folder-atomic@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "dataset", "Original")
    base = f"/api/v1/workspaces/{workspace['id']}/resource-folders"
    method, path, body, expected = {
        "create": ("POST", base, {"resource_type": "dataset", "name": "New"}, 201),
        "rename": ("PATCH", base + "/" + folder["id"], {"name": "Renamed"}, 200),
        "delete": ("DELETE", base + "/" + folder["id"], None, 204),
    }[operation]

    def snapshot():
        return (
            db_session.execute(select(ResourceFolder.id, ResourceFolder.name,
                                      ResourceFolder.parent_folder_id)
                               .order_by(ResourceFolder.id)).all(),
            db_session.execute(select(AuditLog.id).order_by(AuditLog.id)).all(),
        )

    before = snapshot()

    def reject_audit(session, context, instances):
        if any(isinstance(row, AuditLog) for row in session.new):
            raise RuntimeError("synthetic audit persistence failure")

    event.listen(db_session, "before_flush", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="synthetic audit persistence failure"):
            client.request(method, path, headers=headers, json=body)
    finally:
        event.remove(db_session, "before_flush", reject_audit)
        db_session.rollback()
    assert snapshot() == before
    retried = client.request(method, path, headers=headers, json=body)
    assert retried.status_code == expected
    assert len(snapshot()[1]) == len(before[1]) + 1


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                    reason="requires isolated PostgreSQL verification")
@pytest.mark.parametrize("operation", ["create", "rename", "delete"])
def test_postgres_folder_change_is_invisible_until_audit_commits(review_database, operation):
    engine, ids = review_database
    with Session(engine) as seed:
        folder = ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                resource_type="dataset", name="Original")
        seed.add(folder)
        seed.commit()
        folder_id = folder.id

    def snapshot():
        with Session(engine) as observer:
            return (
                observer.execute(select(ResourceFolder.id, ResourceFolder.name)
                                 .order_by(ResourceFolder.id)).all(),
                observer.execute(select(AuditLog.id).order_by(AuditLog.id)).all(),
            )

    before = snapshot()
    observed = []

    def reject_audit(session, context, instances):
        if any(isinstance(row, AuditLog) for row in session.new):
            observed.append(snapshot())
            raise RuntimeError("synthetic audit persistence failure")

    with Session(engine) as db:
        service = ResourceFolderService(db)

        def mutate():
            if operation == "create":
                service.create_folder(workspace_id=ids[0], resource_type="dataset", name="New",
                                      parent_folder_id=None, current_user=db.get(User, ids[2][0]))
            elif operation == "rename":
                service.update_folder(workspace_id=ids[0], folder_id=folder_id, name="Renamed",
                                      parent_folder_id=None, actor_user_id=ids[2][0])
            else:
                service.delete_folder(workspace_id=ids[0], folder_id=folder_id,
                                      actor_user_id=ids[2][0])

        event.listen(db, "before_flush", reject_audit)
        try:
            with pytest.raises(RuntimeError, match="synthetic audit persistence failure"):
                mutate()
        finally:
            event.remove(db, "before_flush", reject_audit)
        assert observed == [before]
        assert snapshot() == before
        assert db.is_active
        mutate()
    assert snapshot()[0] != before[0]
    assert len(snapshot()[1]) == len(before[1]) + 1
