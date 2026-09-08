"""Real pgvector ordering and pre-retrieval scope checks in a disposable schema."""
import os

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.knowledge import DocumentChunk, DocumentVersion, Embedding, KnowledgeDocument
from app.models.workspace import Workspace
from app.services.retrieval_service import RetrievalError, RetrievalService

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires PostgreSQL")


class Provider:
    provider = "fixture"
    model = "two-dimensional"
    dimensions = 2
    calls = 0

    def embed_texts(self, texts):
        self.calls += 1
        return [[1.0, 0.0]]


def add_document(db, ids, vector, title):
    document = KnowledgeDocument(workspace_id=ids[0], created_by_user_id=ids[2][0],
        title=title, language="en", status="indexed")
    db.add(document)
    db.flush()
    version = DocumentVersion(workspace_id=ids[0], knowledge_document_id=document.id,
        version=1, content_hash="a" * 64, content_type="text/plain", raw_text=title)
    db.add(version)
    db.flush()
    chunk = DocumentChunk(workspace_id=ids[0], document_version_id=version.id,
        language="en", chunk_index=0, content=title, token_count=2)
    db.add(chunk)
    db.flush()
    db.add(Embedding(workspace_id=ids[0], document_chunk_id=chunk.id,
        provider="fixture", model="two-dimensional", vector=vector))
    db.commit()
    return document.id


def search(db, ids, provider, allowed=None):
    return RetrievalService(db, provider, strategy="vector", allowed_document_ids=allowed).search(
        workspace_id=ids[0], query="Refund policy?", language=SupportedLanguage.en,
        top_k=1, min_score=0, document_id=None)


def test_sql_ranking_scope_and_empty_selection(review_database):
    engine, ids = review_database
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(engine, "before_cursor_execute", capture)
    try:
        with Session(engine) as db:
            near = add_document(db, ids, [1, 0], "Near")
            far = add_document(db, ids, [-1, 0], "Far")
            provider = Provider()
            assert search(db, ids, provider).results[0].document_id == near
            restricted = search(db, ids, provider, [far])
            assert restricted.results[0].document_id == far
            assert restricted.results[0].vector_score == 0
            calls = provider.calls
            assert search(db, ids, provider, []).no_source
            assert provider.calls == calls
            assert any("<=>" in sql and "ORDER BY" in sql and "LIMIT" in sql
                       for sql in statements)
    finally:
        event.remove(engine, "before_cursor_execute", capture)


def test_invalid_stored_dimensions_fail_before_provider(review_database):
    engine, ids = review_database
    with Session(engine) as db:
        add_document(db, ids, [1, 0, 0], "Wrong dimensions")
        provider = Provider()
        with pytest.raises(RetrievalError, match="dimensions"):
            search(db, ids, provider)
        assert provider.calls == 0


@pytest.mark.parametrize("excluded", ["workspace", "language", "model", "failed", "obsolete"])
def test_sql_excludes_ineligible_vectors_before_validation(review_database, excluded):
    engine, ids = review_database
    with Session(engine) as db:
        eligible = add_document(db, ids, [1, 0], "Current allowed policy")
        bad = add_document(db, ids, [1, 0, 0], "Must never reach retrieval")
        document = db.get(KnowledgeDocument, bad)
        version = db.scalar(select(DocumentVersion).where(
            DocumentVersion.knowledge_document_id == bad))
        chunk = db.scalar(select(DocumentChunk).where(
            DocumentChunk.document_version_id == version.id))
        embedding = db.scalar(select(Embedding).where(Embedding.document_chunk_id == chunk.id))
        if excluded == "workspace":
            foreign = Workspace(name="Foreign workspace", created_by_user_id=ids[2][0])
            db.add(foreign)
            db.flush()
            for entity in (document, version, chunk, embedding):
                entity.workspace_id = foreign.id
        elif excluded == "language":
            document.language = chunk.language = SupportedLanguage.ja
        elif excluded == "model":
            embedding.model = "other-model"
        elif excluded == "failed":
            document.status = "failed"
        else:
            # A newer version without chunks must not revive the obsolete policy.
            db.add(DocumentVersion(workspace_id=ids[0], knowledge_document_id=bad,
                version=2, content_hash="b" * 64, content_type="text/plain", raw_text="New policy"))
        db.commit()
        provider = Provider()
        result = search(db, ids, provider)
        assert [item.document_id for item in result.results] == [eligible]
        assert provider.calls == 1
