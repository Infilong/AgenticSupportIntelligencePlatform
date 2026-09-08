import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.knowledge.ingestion import index_document
from app.modules.knowledge.models import Chunk, Document
from app.modules.knowledge.service import set_withdrawn, upload
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import change_member
from app.providers.local_embeddings import EmbeddingBatch
from app.worker import run_once
from tests.integration.conftest import login


class TestEmbeddings:
    """External-provider test double only; real CPU acceptance is a separate runtime check."""

    __test__ = False

    def token_count(self, text):
        return len(text.split()) + 2

    def encode_batch(self, texts, kind):
        return EmbeddingBatch(
            vectors=[[1.0] + [0.0] * 383 for _ in texts],
            input_tokens=sum(self.token_count(text) for text in texts),
            duration_ms=1,
        )


def ingest(system, provider=None):
    return run_once(
        system["engine"],
        handlers={
            "index_document": lambda engine, job: index_document(engine, job, provider or TestEmbeddings())
        },
    )


def add_version(
    system, content=b"# Policy\n\nRefund requests have a fourteen-day deadline.", document_id=None
):
    with Session(system["engine"], expire_on_commit=False) as db, db.begin():
        version = upload(
            db,
            system["workspace"],
            system["users"]["admin"].id,
            "policy.md",
            content,
            uuid.uuid4().hex,
            document_id,
        )
    return version


def test_original_idempotency_index_and_permission_boundaries(system):
    client, ws = system["client"], system["workspace"]
    auth = login(client)
    headers = {**auth, "Idempotency-Key": "upload-test"}
    original = b"\xef\xbb\xbf# Policy\r\n\r\nOriginal preserved."
    response = client.post(
        f"/api/workspaces/{ws}/documents", headers=headers, files={"file": ("policy.md", original)}
    )
    assert response.status_code == 202, response.text
    data = response.json()
    assert (
        client.post(
            f"/api/workspaces/{ws}/documents", headers=headers, files={"file": ("policy.md", original)}
        ).json()
        == data
    )
    assert (
        client.post(
            f"/api/workspaces/{ws}/documents", headers=headers, files={"file": ("policy.md", b"changed")}
        ).status_code
        == 409
    )
    assert ingest(system)
    path = f"/api/workspaces/{ws}/documents/{data['document_id']}/versions/{data['version_id']}"
    assert client.get(path + "/original").content == original
    assert client.get(path).json()["text"] == "# Policy\n\nOriginal preserved."
    with Session(system["engine"]) as db:
        chunk = db.scalar(select(Chunk))
        assert len(chunk.embedding) == 384
        assert chunk.text == "# Policy\n\nOriginal preserved."
        call = db.scalar(select(ModelCall))
        assert call.status == "succeeded" and call.input_tokens > 0 and call.job_attempt == 1
    viewer = login(client, "viewer")
    assert client.get(path).status_code == 200
    assert (
        client.post(
            f"/api/workspaces/{ws}/documents",
            headers={**viewer, "Idempotency-Key": "denied"},
            files={"file": ("policy.md", b"denied")},
        ).status_code
        == 403
    )
    login(client, "other")
    assert client.get(path).status_code == 404
    assert client.get(path + "/original").status_code == 404


def test_failed_replacement_preserves_active_content_and_records_failure(system):
    first = add_version(system)
    assert ingest(system)
    replacement = add_version(system, b"# Replacement\nNew policy.", first.document_id)

    class Broken(TestEmbeddings):
        def encode_batch(self, texts, kind):
            raise RuntimeError("sensitive input must not enter operational logs")

    assert ingest(system, Broken())
    with Session(system["engine"]) as db:
        document = db.get(Document, first.document_id)
        assert document.active_version_id == first.id
        assert db.get(Job, replacement.job_id).state == "failed"
        assert db.scalar(select(ModelCall).where(ModelCall.job_id == replacement.job_id)).status == "failed"
        assert (
            db.scalar(select(func.count()).select_from(Chunk).where(Chunk.version_id == replacement.id)) == 0
        )


@pytest.mark.parametrize("intervention", ["withdraw", "replace", "demote"])
def test_inflight_version_cannot_activate_after_intervention(system, intervention):
    first = add_version(system)
    assert ingest(system)
    second = add_version(system, b"# Second\nSecond policy version.", first.document_id)
    entered, release = Event(), Event()

    class Paused(TestEmbeddings):
        def encode_batch(self, texts, kind):
            entered.set()
            assert release.wait(timeout=15)
            return super().encode_batch(texts, kind)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(ingest, system, Paused())
        try:
            assert entered.wait(timeout=10)
            if intervention == "replace":
                third = add_version(system, b"# Third\nThird policy version.", first.document_id)
            elif intervention == "demote":
                with Session(system["engine"]) as db:
                    change_member(
                        db,
                        system["workspace"],
                        system["users"]["admin"].id,
                        system["users"]["operator"].id,
                        "admin",
                    )
                    change_member(
                        db,
                        system["workspace"],
                        system["users"]["operator"].id,
                        system["users"]["admin"].id,
                        "operator",
                    )
            else:
                with Session(system["engine"]) as db, db.begin():
                    set_withdrawn(
                        db, system["workspace"], system["users"]["admin"].id, first.document_id, True
                    )
        finally:
            release.set()
        assert future.result(timeout=10)
    with Session(system["engine"]) as db:
        assert db.get(Document, first.document_id).active_version_id == first.id
        assert db.get(Job, second.job_id).state == ("failed" if intervention == "demote" else "cancelled")
        assert db.scalar(select(func.count()).select_from(Chunk).where(Chunk.version_id == second.id)) == 0
    if intervention == "replace":
        assert ingest(system)
        with Session(system["engine"]) as db:
            assert db.get(Document, first.document_id).active_version_id == third.id


def test_database_rejects_cross_document_active_pointer(system):
    first, second = add_version(system), add_version(system)
    with pytest.raises(IntegrityError), Session(system["engine"]) as db, db.begin():
        db.get(Document, first.document_id).active_version_id = second.id
        db.flush()


def test_upload_validation_and_total_body_limit(system):
    client, ws = system["client"], system["workspace"]
    headers = {**login(client), "Idempotency-Key": "invalid"}
    for filename, data, expected in [
        ("policy.pdf", b"pdf", 415),
        ("policy.txt", b"\xff", 400),
        ("policy.txt", b"\x00", 400),
        ("policy.txt", b" ", 400),
    ]:
        assert (
            client.post(
                f"/api/workspaces/{ws}/documents", headers=headers, files={"file": (filename, data)}
            ).status_code
            == expected
        )
    assert (
        client.post(
            f"/api/workspaces/{ws}/documents",
            headers=headers,
            files={"file": ("huge.txt", b"x" * (6 * 1024 * 1024))},
        ).status_code
        == 413
    )
