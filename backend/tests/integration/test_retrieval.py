import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge.models import Chunk
from app.modules.knowledge.retrieval import retrieve
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.knowledge.service import set_withdrawn
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import change_member
from tests.integration.test_knowledge import TestEmbeddings, add_version, ingest


def search(system, **kwargs):
    return retrieve(
        system["engine"],
        system["workspace"],
        system["users"]["viewer"].id,
        "refund deadline",
        provider=TestEmbeddings(),
        **kwargs,
    )


def test_real_sql_vector_ranking_active_filters_and_ledger(system):
    first = add_version(system)
    ingest(system)
    second = add_version(system, b"# Current\nRefund deadline is thirty days.", first.document_id)
    ingest(system)
    unrelated = add_version(system, b"# Cafeteria\nLunch is served at noon.")
    ingest(system)
    with Session(system["engine"]) as db, db.begin():
        chunk = db.scalar(select(Chunk).where(Chunk.version_id == unrelated.id))
        chunk.embedding = [0.0, 1.0] + [0.0] * 382
    result = search(system)
    assert result["results"][0]["version_id"] == str(second.id)
    assert str(first.id) not in {row["version_id"] for row in result["results"]}
    assert result["results"][0]["cosine_similarity"] > 0.99
    with Session(system["engine"]) as db:
        trace = db.get(RetrievalTrace, result["trace_id"])
        assert trace.status == "succeeded" and trace.results
        assert "text" not in trace.results[0]
        call = db.scalar(select(ModelCall).where(ModelCall.retrieval_id == trace.id))
        assert call.status == "succeeded" and call.operation == "embed_query"
    with Session(system["engine"]) as db, db.begin():
        set_withdrawn(db, system["workspace"], system["users"]["admin"].id, first.document_id, True)
    assert str(second.id) not in {row["version_id"] for row in search(system)["results"]}


def test_foreign_permission_is_checked_before_embedding(system):
    class ForbiddenProvider:
        def encode_batch(self, *_):
            raise AssertionError("Unauthorized query reached model")

    with pytest.raises(HTTPException) as failure:
        retrieve(
            system["engine"],
            system["foreign"],
            system["users"]["viewer"].id,
            "secret",
            provider=ForbiddenProvider(),
        )
    assert failure.value.status_code == 404


def test_best_matching_foreign_chunk_never_enters_authorized_results(system):
    foreign = {
        **system,
        "workspace": system["foreign"],
        "users": {**system["users"], "admin": system["users"]["other"]},
    }
    secret = add_version(foreign, b"# Private\nRefund deadline: secret company terms.")
    ingest(foreign)
    assert search(system)["results"] == []
    own = add_version(system)
    ingest(system)
    results = search(system)["results"]
    assert {row["version_id"] for row in results} == {str(own.id)}
    assert str(secret.id) not in {row["version_id"] for row in results}


def test_empty_and_failed_retrieval_are_distinct(system):
    assert search(system)["status"] == "no_sources"

    class Broken(TestEmbeddings):
        def encode_batch(self, *_):
            raise OSError("model missing")

    with pytest.raises(OSError):
        retrieve(
            system["engine"],
            system["workspace"],
            system["users"]["viewer"].id,
            "refund deadline",
            provider=Broken(),
        )
    with Session(system["engine"]) as db:
        failed = db.scalar(select(RetrievalTrace).where(RetrievalTrace.status == "failed"))
        assert failed.error_code == "OSError"


def test_revocation_during_embedding_prevents_source_materialization(system):
    add_version(system)
    ingest(system)

    class Revoked(TestEmbeddings):
        def encode_batch(self, texts, kind):
            with Session(system["engine"]) as db:
                change_member(
                    db, system["workspace"], system["users"]["admin"].id, system["users"]["viewer"].id, None
                )
            return super().encode_batch(texts, kind)

    with pytest.raises(HTTPException) as failure:
        retrieve(
            system["engine"],
            system["workspace"],
            system["users"]["viewer"].id,
            "refund deadline",
            provider=Revoked(),
        )
    assert failure.value.status_code == 404
    with Session(system["engine"]) as db:
        trace = db.scalar(select(RetrievalTrace))
        assert trace.status == "failed" and trace.results == []
