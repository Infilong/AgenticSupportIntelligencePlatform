import os

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_knowledge_documents import auth_headers, create_workspace, login, register
from test_resource_folders import create_folder
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.audit import AuditLog
from app.models.folder import ResourceFolder
from app.models.knowledge import DocumentChunk, DocumentVersion, Embedding, KnowledgeDocument
from app.models.user import User
from app.services.knowledge_service import KnowledgeService


@pytest.mark.parametrize("operation", ["upload", "reindex", "move", "delete"])
def test_document_audit_failure_preserves_index_and_allows_retry(client, db_session, operation):
    register(client, "knowledge-atomic@example.test")
    token = login(client, "knowledge-atomic@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    folder = create_folder(client, token, workspace["id"], "knowledge_document", "Destination")
    base = f"/api/v1/workspaces/{workspace['id']}/knowledge-documents"
    uploaded = client.post(base, headers=headers, json={
        "title": "Refund policy", "content_type": "text/plain", "language": "en",
        "content": "Refunds are available within seven days.",
    })
    assert uploaded.status_code == 201
    assert uploaded.json()["embedding_count"] > 0
    path = base + "/" + uploaded.json()["document"]["id"]
    method, body, expected = "DELETE", None, 204
    if operation == "move":
        method, path, body, expected = "PATCH", path + "/folder", {"folder_id": folder["id"]}, 200
    elif operation in ("upload", "reindex"):
        method, path, expected = "POST", (base if operation == "upload" else path + "/reindex"), 201
        if operation == "reindex":
            expected = 200
        body = {"title": "Updated policy", "content_type": "text/plain", "language": "en",
                "content": "Refunds are available within fourteen days."}

    def snapshot():
        db_session.expire_all()
        return [db_session.execute(select(*model.__table__.c).order_by(model.id)).all()
                for model in (KnowledgeDocument, DocumentVersion, DocumentChunk,
                              Embedding, AuditLog)]

    before = snapshot()

    def reject_audit(session, context, instances):
        if any(isinstance(row, AuditLog) for row in session.new):
            raise RuntimeError("synthetic document audit failure")

    event.listen(db_session, "before_flush", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="synthetic document audit failure"):
            client.request(method, path, headers=headers, json=body)
    finally:
        event.remove(db_session, "before_flush", reject_audit)
        db_session.rollback()
    assert snapshot() == before
    response = client.request(method, path, headers=headers, json=body)
    assert response.status_code == expected, response.text
    assert len(snapshot()[-1]) == len(before[-1]) + 1


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                    reason="requires isolated PostgreSQL verification")
@pytest.mark.parametrize("operation", ["move", "delete"])
def test_postgres_document_audit_visibility_and_rollback(review_database, operation):
    engine, ids = review_database
    with Session(engine) as seed:
        folder = ResourceFolder(workspace_id=ids[0], created_by_user_id=ids[2][0],
                                resource_type="knowledge_document", name="Destination")
        seed.add(folder)
        seed.commit()
        folder_id = folder.id
        result = KnowledgeService(seed).upload_document(
            workspace_id=ids[0], title="Policy", content_type="text/plain",
            content="Refunds are available within seven days.", language=SupportedLanguage.en,
            current_user=seed.get(User, ids[2][0]),
        )
        document_id = result.document.id
        assert result.embedding_count > 0

    def snapshot():
        with Session(engine) as observer:
            return [observer.execute(select(*model.__table__.c).order_by(model.id)).all()
                    for model in (KnowledgeDocument, DocumentVersion, DocumentChunk,
                                  Embedding, AuditLog)]

    before = snapshot()
    observed = []

    def reject_audit(session, context, instances):
        if any(isinstance(row, AuditLog) for row in session.new):
            observed.append(snapshot())
            raise RuntimeError("synthetic document audit failure")

    with Session(engine) as db:
        service = KnowledgeService(db)

        def mutate():
            args = {"workspace_id": ids[0], "document_id": document_id,
                    "actor_user_id": ids[2][0]}
            if operation == "move":
                return service.move_document(**args, folder_id=folder_id)
            return service.delete_document(**args)

        event.listen(db, "before_flush", reject_audit)
        try:
            with pytest.raises(RuntimeError, match="synthetic document audit failure"):
                mutate()
        finally:
            event.remove(db, "before_flush", reject_audit)
        assert observed == [before]
        assert snapshot() == before
        assert db.is_active
        mutate()
    after = snapshot()
    assert after[0] != before[0]
    assert len(after[-1]) == len(before[-1]) + 1
    assert after[-1][-1].actor_user_id == ids[2][0]
