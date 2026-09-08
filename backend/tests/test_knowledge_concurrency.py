"""Overlapping reindex requests must allocate distinct versions from fresh state."""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from test_review_transactions import review_database as review_database

from app.core.language import SupportedLanguage
from app.models.knowledge import DocumentVersion, KnowledgeDocument
from app.models.user import User
from app.services.embedding_provider import MockEmbeddingProvider
from app.services.knowledge_service import KnowledgeService

pytestmark = pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1",
                                reason="requires isolated PostgreSQL verification")


def test_overlapping_reindex_allocates_versions_and_preserves_new_metadata(review_database):
    engine, ids = review_database
    with Session(engine) as seed:
        result = KnowledgeService(seed).upload_document(
            workspace_id=ids[0], title="Original", content_type="text/plain",
            content="Original refund policy.", language=SupportedLanguage.en,
            current_user=seed.get(User, ids[2][0]),
        )
        document_id = result.document.id
    entered, release, ready = Event(), Event(), Event()
    second_pid = []

    class PausedProvider(MockEmbeddingProvider):
        def embed_texts(self, texts):
            entered.set()
            assert release.wait(timeout=15), "test did not release first provider"
            return super().embed_texts(texts)

    def first():
        with Session(engine) as db:
            return KnowledgeService(db, PausedProvider()).reindex_document(
                workspace_id=ids[0], document_id=document_id, actor_user_id=ids[2][0],
                title="New title", content="First revision.",
            ).latest_version.version

    def second():
        with Session(engine) as db:
            cached = db.get(KnowledgeDocument, document_id)
            assert cached.title == "Original"
            second_pid.append(db.scalar(text("select pg_backend_pid()")))
            ready.set()
            result = KnowledgeService(db).reindex_document(
                workspace_id=ids[0], document_id=document_id, actor_user_id=ids[2][0],
                content="Second revision.",
            )
            return result.latest_version.version, result.document.title

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_result = pool.submit(first)
        try:
            assert entered.wait(timeout=10)
            second_result = pool.submit(second)
            assert ready.wait(timeout=10)
            blocked = False
            deadline = time.monotonic() + 3
            with engine.connect() as observer:
                while time.monotonic() < deadline:
                    blocked = bool(observer.scalar(
                        text("select cardinality(pg_blocking_pids(:pid))"), {"pid": second_pid[0]},
                    ))
                    if blocked:
                        break
                    time.sleep(0.01)
            assert blocked, "second transaction never overlapped the first document mutation"
        finally:
            release.set()
        assert first_result.result(timeout=10) == 2
        assert second_result.result(timeout=10) == (3, "New title")
    with Session(engine) as db:
        versions = db.scalars(select(DocumentVersion).where(
            DocumentVersion.knowledge_document_id == document_id,
        ).order_by(DocumentVersion.version)).all()
        assert [row.version for row in versions] == [1, 2, 3]
        assert [row.raw_text for row in versions] == [
            "Original refund policy.", "First revision.", "Second revision.",
        ]
