"""Denied knowledge management requests must never enter the domain service."""

from uuid import UUID

import pytest
from sqlalchemy import select
from test_knowledge_documents import auth_headers, create_workspace, login, register

from app.models.ai import AIRun
from app.models.audit import AuditLog
from app.models.knowledge import DocumentChunk, DocumentVersion, Embedding, KnowledgeDocument
from app.models.workspace import WorkspaceMember, WorkspaceRole
from app.services.knowledge_service import KnowledgeService


@pytest.mark.parametrize("actor,status,operations", [
    ("anonymous", 401, ("upload", "reindex", "move", "delete")),
    ("outsider", 404, ("upload", "reindex", "move", "delete")),
    ("viewer", 403, ("upload", "reindex", "move", "delete")),
    ("reviewer", 403, ("upload", "reindex", "move", "delete")),
    ("member", 403, ("move", "delete")),
    ("developer", 403, ("delete",)),
])
def test_denied_knowledge_writes_preserve_index_and_never_enter_service(
    client, db_session, monkeypatch, actor, status, operations,
):
    register(client, "knowledge-owner@example.test")
    owner = login(client, "knowledge-owner@example.test")
    workspace = create_workspace(client, owner)
    base = f"/api/v1/workspaces/{workspace['id']}/knowledge-documents"
    payload = {"title": "Protected refund policy", "content_type": "text/plain",
               "content": "Refunds are available within seven days.", "language": "en"}
    uploaded = client.post(base, headers=auth_headers(owner), json=payload)
    assert uploaded.status_code == 201, uploaded.text
    document_id = uploaded.json()["document"]["id"]
    detail = client.get(f"{base}/{document_id}", headers=auth_headers(owner))
    assert detail.status_code == 200
    assert detail.json()["chunks"]
    assert detail.json()["embedding_count"] > 0

    headers = {}
    if actor != "anonymous":
        user = register(client, "knowledge-reader@example.test")
        headers = auth_headers(login(client, "knowledge-reader@example.test"))
        if actor != "outsider":
            db_session.add(WorkspaceMember(
                workspace_id=UUID(workspace["id"]), user_id=UUID(user["id"]),
                role=WorkspaceRole(actor),
            ))
            db_session.commit()
            allowed_read = client.get(f"{base}/{document_id}", headers=headers)
            assert allowed_read.status_code == 200
            assert allowed_read.json()["chunks"]

    def snapshot():
        db_session.expire_all()
        return [db_session.execute(select(*model.__table__.c).order_by(model.id)).all()
                for model in (KnowledgeDocument, DocumentVersion, DocumentChunk,
                              Embedding, AIRun, AuditLog)]

    before = snapshot()
    entered = []
    for name in ("upload_document", "reindex_document", "move_document", "delete_document"):
        original = getattr(KnowledgeService, name)

        def observe(self, _name=name, _original=original, **kwargs):
            entered.append(_name)
            return _original(self, **kwargs)

        monkeypatch.setattr(KnowledgeService, name, observe)

    requests = {
        "upload": ("POST", base, payload),
        "reindex": ("POST", f"{base}/{document_id}/reindex", {**payload, "content": "Changed."}),
        "move": ("PATCH", f"{base}/{document_id}/folder", {"folder_id": None}),
        "delete": ("DELETE", f"{base}/{document_id}", None),
    }
    for operation in operations:
        method, path, body = requests[operation]
        response = client.request(method, path, headers=headers, json=body)
        assert response.status_code == status, response.text
        assert entered == []
        assert snapshot() == before
