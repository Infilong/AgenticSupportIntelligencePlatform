"""Migration round-trip and retained original-byte invariants on PostgreSQL."""
import hashlib
import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge_upload import KnowledgeUpload
from app.models.user import User
from app.models.workspace import Workspace


@pytest.mark.skipif(os.environ.get("RUN_POSTGRES_TESTS") != "1", reason="requires PostgreSQL")
def test_upload_migration_preserves_binary_and_rejects_invalid_ready():
    url = make_url(get_settings().database_url)
    assert url.get_backend_name() == "postgresql"
    name = "upload_test_" + uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    target = create_engine(url.set(database=name))
    environment = {**os.environ, "DATABASE_URL": url.set(database=name).render_as_string(
        hide_password=False)}

    def migrate(command, revision, success=True):
        result = subprocess.run([sys.executable, "-m", "alembic", command, revision],
            env=environment, capture_output=True, text=True, timeout=60)
        assert (result.returncode == 0) is success, result.stderr
        return result

    try:
        migrate("upgrade", "0039_record_clarification")
        with Session(target) as db:
            user = User(email="upload@example.test", display_name="Owner", password_hash="unused")
            db.add(user)
            db.flush()
            workspace = Workspace(name="Retained workspace", created_by_user_id=user.id)
            db.add(workspace)
            db.commit()
            owner_id, workspace_id = user.id, workspace.id
        migrate("upgrade", "0040_knowledge_uploads")
        migrate("downgrade", "0039_record_clarification")
        migrate("upgrade", "0040_knowledge_uploads")
        original = b"\x00\xff\r\n" + "会社政策 公司政策".encode()
        with Session(target) as db:
            assert db.get(Workspace, workspace_id).name == "Retained workspace"
            upload = KnowledgeUpload(workspace_id=workspace_id, created_by_user_id=owner_id,
                request_key="upload", request_hash="f" * 64, filename="policy.doc",
                title="Policy", content_type="application/msword", language="ja",
                original_sha256=hashlib.sha256(original).hexdigest(), original_bytes=original)
            db.add(upload)
            db.commit()
            upload_id = upload.id
        with Session(target) as db:
            upload = db.scalar(select(KnowledgeUpload).where(KnowledgeUpload.id == upload_id))
            assert "original_bytes" in inspect(upload).unloaded
            assert upload.original_bytes == original
            upload.state = "ready"
            with pytest.raises(IntegrityError, match="ck_knowledge_upload_ready"):
                db.commit()
            db.rollback()
            assert db.get(KnowledgeUpload, upload_id).state == "uploaded"
            upload = db.get(KnowledgeUpload, upload_id)
            upload.original_bytes = b""
            with pytest.raises(IntegrityError, match="ck_knowledge_upload_size"):
                db.commit()
            db.rollback()
        refused = migrate("downgrade", "0039_record_clarification", success=False)
        assert "Cannot discard uploaded originals" in refused.stderr
        with Session(target) as db:
            assert db.get(KnowledgeUpload, upload_id).original_bytes == original
            assert db.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0040_knowledge_uploads")
    finally:
        target.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()
