"""Verify real pgvector storage and downgrade refusal in a disposable database."""

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus
from app.models.knowledge import (
    DocumentChunk,
    DocumentStatus,
    DocumentVersion,
    Embedding,
    KnowledgeDocument,
)
from app.models.retrieval import RetrievalTrace
from app.models.user import User
from app.models.workspace import Workspace


def seed_embedding(engine):
    with Session(engine) as db:
        user = User(email="migration@example.com", display_name="Migration", password_hash="unused")
        db.add(user)
        db.flush()
        workspace = Workspace(name="Migration", created_by_user_id=user.id)
        db.add(workspace)
        db.flush()
        document = KnowledgeDocument(workspace_id=workspace.id, title="Policy",
                                     language=SupportedLanguage.en, status=DocumentStatus.indexed,
                                     created_by_user_id=user.id)
        db.add(document)
        db.flush()
        version = DocumentVersion(workspace_id=workspace.id, knowledge_document_id=document.id,
                                  version=1, content_hash="a" * 64, content_type="text/plain",
                                  raw_text="Refund policy")
        db.add(version)
        db.flush()
        chunk = DocumentChunk(workspace_id=workspace.id, document_version_id=version.id,
                              language=SupportedLanguage.en, chunk_index=0,
                              content="Refund policy", token_count=2)
        db.add(chunk)
        db.flush()
        embedding = Embedding(workspace_id=workspace.id, document_chunk_id=chunk.id,
                              provider="mock", model="mock-16", vector=[0.125] * 16)
        db.add(embedding)
        db.commit()
        return embedding.id


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_embedding_upgrade_preserves_vectors_and_refuses_lossy_downgrade():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "embedding_migration_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}

    def migrate(command, revision, *, success=True):
        result = subprocess.run(["alembic", command, revision], env=environment,
                                capture_output=True, text=True, timeout=60)
        assert (result.returncode == 0) is success, result.stderr
        return result

    def stored():
        with target.connect() as connection:
            return connection.execute(text(
                "SELECT vector::text, vector_dims(vector) FROM embeddings"
            )).one()

    try:
        migrate("upgrade", "0026_model_call_reservations")
        embedding_id = seed_embedding(target)
        original = stored()
        migrate("upgrade", "head")
        assert stored() == original
        # Prove safe downgrade preserves existing user rows and vector contents.
        migrate("downgrade", "0026_model_call_reservations")
        assert stored() == original
        migrate("upgrade", "head")
        with Session(target) as db:
            embedding = db.get(Embedding, embedding_id)
            embedding.vector = [0.25] * 1536
            embedding.model = "semantic-test-1536"
            db.commit()
        assert stored()[1] == 1536
        rejected = migrate("downgrade", "0026_model_call_reservations", success=False)
        assert "non-16-dimensional vectors exist" in rejected.stderr
        assert stored()[1] == 1536
        with Session(target) as db:
            assert db.scalar(select(Embedding)).vector == [0.25] * 1536
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0032_execution_ownership")
            embedding = db.get(Embedding, embedding_id)
            attempt = AIRun(workspace_id=embedding.workspace_id, provider="openai",
                model="text-embedding-3-small", purpose="embedding_query", language="en",
                status=AIRunStatus.pending, prompt_tokens=10, completion_tokens=0,
                total_tokens=10, estimated_cost=0.00001, latency_ms=0, cache_hit=False)
            db.add(attempt)
            db.commit()
            attempt_id = attempt.id
        rejected = migrate("downgrade", "0027_embedding_dimensions", success=False)
        assert "unresolved attempts exist" in rejected.stderr
        with Session(target) as db:
            assert db.get(AIRun, attempt_id).status == AIRunStatus.pending
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0032_execution_ownership")
            db.get(AIRun, attempt_id).status = AIRunStatus.succeeded
            db.commit()
        migrate("downgrade", "0027_embedding_dimensions")
        migrate("upgrade", "head")
        with Session(target) as db:
            assert db.get(AIRun, attempt_id).status == AIRunStatus.succeeded
            migration_workspace_id = db.get(AIRun, attempt_id).workspace_id
        migrate("downgrade", "0028_ai_attempt_status")
        with target.begin() as connection:
            trace_id = uuid4()
            connection.execute(text("""INSERT INTO retrieval_traces
                (id, workspace_id, query, language, strategy, filters_json, latency_ms,
                 no_source, created_at) VALUES
                (:id, :workspace, 'Policy?', 'en', 'lexical', '{}', 1, true, now())"""),
                {"id": trace_id, "workspace": migration_workspace_id})
        migrate("upgrade", "head")
        with Session(target) as db:
            trace = db.get(RetrievalTrace, trace_id)
            assert trace.outcome == "unknown" and trace.error_code is None
            trace.outcome, trace.error_code = "failed", "embedding_failed"
            db.commit()
        rejected = migrate("downgrade", "0028_ai_attempt_status", success=False)
        assert "failed or pending traces" in rejected.stderr
        with Session(target) as db:
            trace = db.get(RetrievalTrace, trace_id)
            assert trace.outcome == "failed" and trace.query == "Policy?"
            # Synthetic fixture transitions to exercise the safe downgrade path.
            trace.outcome, trace.error_code = "succeeded", None
            db.commit()
        migrate("downgrade", "0028_ai_attempt_status")
        migrate("upgrade", "head")
        with Session(target) as db:
            assert db.get(RetrievalTrace, trace_id).query == "Policy?"
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
