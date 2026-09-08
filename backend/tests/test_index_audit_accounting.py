"""PostgreSQL: failed publication rolls back indexes, not independently billed usage."""

import os
from uuid import UUID

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_embedding_runtime import configured_client as configured_client
from test_knowledge_documents import auth_headers, create_workspace, login, register
from test_review_transactions import review_database as review_database

from app.models.ai import AIRun, AIRunStatus
from app.models.audit import AuditLog
from app.models.knowledge import DocumentChunk, DocumentVersion, Embedding, KnowledgeDocument
from app.services.embedding_transport import OpenAIEmbeddingTransport

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


@pytest.mark.parametrize("operation", ["upload", "reindex"])
def test_failed_index_audit_retains_usage_and_hides_publication(
    configured_client, monkeypatch, operation,
):
    client, engine = configured_client

    def synthetic(self, **kwargs):
        return {"model": kwargs["model"], "usage": {"prompt_tokens": 1, "total_tokens": 1},
                "data": [{"index": i, "embedding": [1.0, 0.0, 0.0, 0.0]}
                         for i, _ in enumerate(kwargs["texts"])]}

    monkeypatch.setattr(OpenAIEmbeddingTransport, "create", synthetic)
    user = register(client, "index-audit@example.test")
    token = login(client, "index-audit@example.test")
    headers = auth_headers(token)
    workspace = create_workspace(client, token)
    base = f"/api/v1/workspaces/{workspace['id']}/knowledge-documents"
    payload = {"title": "Original", "language": "en", "content_type": "text/plain",
               "content": "Refunds are available within seven days."}
    seeded = client.post(base, headers=headers, json=payload)
    assert seeded.status_code == 201
    document_id = seeded.json()["document"]["id"]
    path = base if operation == "upload" else f"{base}/{document_id}/reindex"
    payload = {**payload, "title": "Updated", "content": "Refunds are available within two days."}

    def snapshot():
        with Session(engine) as observer:
            return [observer.execute(select(*model.__table__.c).order_by(model.id)).all()
                    for model in (KnowledgeDocument, DocumentVersion, DocumentChunk,
                                  Embedding, AuditLog)]

    before = snapshot()
    with Session(engine) as observer:
        old_runs = set(observer.scalars(select(AIRun.id)).all())
    observed = []

    def reject_audit(db, context, instances):
        if any(isinstance(row, AuditLog) and row.workspace_id == UUID(workspace["id"])
               for row in db.new):
            observed.append(snapshot())
            raise RuntimeError("synthetic index audit failure")

    event.listen(Session, "before_flush", reject_audit)
    try:
        with pytest.raises(RuntimeError, match="synthetic index audit failure"):
            client.post(path, headers=headers, json=payload)
    finally:
        event.remove(Session, "before_flush", reject_audit)
    assert observed == [before]
    assert snapshot() == before
    with Session(engine) as observer:
        run, = observer.scalars(select(AIRun).where(AIRun.id.not_in(old_runs))).all()
        assert run.status == AIRunStatus.succeeded
        assert run.total_tokens == 1
        assert run.workspace_id == UUID(workspace["id"])
    retried = client.post(path, headers=headers, json=payload)
    assert retried.status_code == (201 if operation == "upload" else 200)
    after = snapshot()
    added = [row for row in after[-1] if row.id not in {old.id for old in before[-1]}]
    audit, = added
    assert audit.actor_user_id == UUID(user["id"])
    action = "uploaded" if operation == "upload" else "reindexed"
    assert audit.action == f"knowledge_document.{action}"
