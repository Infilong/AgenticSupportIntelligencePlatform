"""Real API permissions must stop folder writes before domain execution."""

from uuid import UUID

import pytest
from sqlalchemy import select
from test_resource_folders import auth_headers, create_folder, create_workspace, login, register

from app.models.audit import AuditLog
from app.models.folder import ResourceFolder
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.folder_service import ResourceFolderService


@pytest.mark.parametrize("resource_type", [
    "knowledge_document", "dataset", "agent_config", "evaluation_run",
])
@pytest.mark.parametrize("actor,status", [
    ("anonymous", 401), ("outsider", 404), ("viewer", 403), ("reviewer", 403),
])
def test_folder_mutations_deny_before_service(
    client, db_session, monkeypatch, resource_type, actor, status,
):
    register(client, "folder-boundary-owner@example.test")
    owner = login(client, "folder-boundary-owner@example.test")
    workspace = create_workspace(client, owner)
    folder = create_folder(client, owner, workspace["id"], resource_type, "Protected folder")
    base = f"/api/v1/workspaces/{workspace['id']}/resource-folders"
    owner_read = client.get(base, headers=auth_headers(owner),
                            params={"resource_type": resource_type})
    assert owner_read.status_code == 200
    assert any(row["id"] == folder["id"] for row in owner_read.json())

    headers = {}
    if actor != "anonymous":
        user = register(client, "folder-boundary-reader@example.test")
        headers = auth_headers(login(client, "folder-boundary-reader@example.test"))
        if actor != "outsider":
            db_session.add(WorkspaceMember(
                workspace_id=UUID(workspace["id"]), user_id=UUID(user["id"]),
                role=WorkspaceRole(actor),
            ))
            db_session.commit()

    def snapshot():
        db_session.expire_all()
        folders = db_session.execute(select(
            ResourceFolder.id, ResourceFolder.workspace_id, ResourceFolder.name,
            ResourceFolder.parent_folder_id, ResourceFolder.updated_at,
        ).order_by(ResourceFolder.id)).all()
        audits = db_session.execute(select(
            AuditLog.id, AuditLog.action, AuditLog.metadata_json,
        ).order_by(AuditLog.id)).all()
        return folders, audits

    before = snapshot()
    entered = []
    for method in ("create_folder", "update_folder", "delete_folder"):
        original = getattr(ResourceFolderService, method)

        def observe(self, _method=method, _original=original, **kwargs):
            entered.append(_method)
            return _original(self, **kwargs)

        monkeypatch.setattr(ResourceFolderService, method, observe)

    for method, path, payload in (
        ("POST", base, {"resource_type": resource_type, "name": "Forbidden folder"}),
        ("PATCH", base + "/" + folder["id"], {"name": "Forbidden rename"}),
        ("DELETE", base + "/" + folder["id"], None),
    ):
        response = client.request(method, path, headers=headers, json=payload)
        assert response.status_code == status, response.text
        assert entered == []
        assert snapshot() == before
