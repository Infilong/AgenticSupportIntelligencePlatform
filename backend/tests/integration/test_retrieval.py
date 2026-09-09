import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.knowledge.models import Chunk, Document
from app.modules.knowledge.retrieval import retrieve
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.knowledge.service import set_withdrawn
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import change_member
from app.providers.local_reranker import InvalidRerankResult, RerankBatch
from tests.integration.conftest import login
from tests.integration.test_knowledge import TestEmbeddings, add_version, ingest


class TestReranker:
    __test__ = False

    def score(self, query, passages):
        return RerankBatch([float(len(passages) - i) for i in range(len(passages))], 10, 1)


def search(system, ranking_provider=None, **kwargs):
    return retrieve(
        system["engine"],
        system["workspace"],
        system["users"]["viewer"].id,
        "refund deadline",
        provider=TestEmbeddings(),
        ranking_provider=ranking_provider or TestReranker(),
        **kwargs,
    )


def ingest_checked(system, version):
    worked = ingest(system)
    with Session(system["engine"]) as db:
        job = db.get(Job, version.job_id)
        document = db.get(Document, version.document_id)
        chunks = db.scalar(select(func.count()).select_from(Chunk).where(Chunk.version_id == version.id))
        diagnostic = {
            "worked": worked,
            "job_state": job.state,
            "attempts": job.attempts,
            "error_code": job.error_code,
            "available_at": str(job.available_at),
            "database_now": str(db.scalar(select(func.clock_timestamp()))),
            "active_version": str(document.active_version_id),
            "expected_version": str(version.id),
            "chunks": chunks,
        }
        assert worked and job.state == "succeeded" and document.active_version_id == version.id and chunks, (
            diagnostic
        )


def test_real_sql_vector_ranking_active_filters_and_ledger(system):
    first = add_version(system)
    ingest_checked(system, first)
    second = add_version(system, b"# Current\nRefund deadline is thirty days.", first.document_id)
    ingest_checked(system, second)
    unrelated = add_version(system, b"# Cafeteria\nLunch is served at noon.")
    ingest_checked(system, unrelated)
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
        call = db.scalar(
            select(ModelCall).where(ModelCall.retrieval_id == trace.id, ModelCall.operation == "embed_query")
        )
        assert call.status == "succeeded" and call.operation == "embed_query"
        ranked = db.scalar(
            select(ModelCall).where(ModelCall.retrieval_id == trace.id, ModelCall.operation == "rerank")
        )
        assert ranked.status == "succeeded" and ranked.input_tokens == 10
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


@pytest.mark.parametrize("change", ["withdraw", "replace", "revoke"])
def test_rerank_revalidates_sources_and_permissions_after_inference(system, change):
    original = add_version(system)
    ingest(system)
    with Session(system["engine"]) as db:
        assert db.scalar(select(Chunk).where(Chunk.version_id == original.id)) is not None

    class Changed(TestReranker):
        def score(self, query, passages):
            if change == "replace":
                add_version(system, b"# Replacement\nNew active policy.", original.document_id)
                ingest(system)
            elif change == "withdraw":
                with Session(system["engine"]) as db, db.begin():
                    set_withdrawn(
                        db, system["workspace"], system["users"]["admin"].id, original.document_id, True
                    )
            else:
                with Session(system["engine"]) as db:
                    change_member(
                        db,
                        system["workspace"],
                        system["users"]["admin"].id,
                        system["users"]["viewer"].id,
                        None,
                    )
            return super().score(query, passages)

    if change == "revoke":
        with pytest.raises(HTTPException) as failure:
            search(system, ranking_provider=Changed())
        assert failure.value.status_code == 404
    else:
        result = search(system, ranking_provider=Changed())
        assert result["status"] == "sources_changed" and result["results"] == []
    with Session(system["engine"]) as db:
        call = db.scalar(select(ModelCall).where(ModelCall.operation == "rerank"))
        assert call.status == "succeeded"  # Actual model work survives denied publication.


@pytest.mark.parametrize("scores", [[], [float("nan")], [float("inf")]])
def test_malformed_reranking_is_an_explicit_recorded_failure(system, scores):
    version = add_version(system)
    ingest_checked(system, version)

    class Malformed(TestReranker):
        def score(self, *_):
            return RerankBatch(scores, 10, 1)

    with pytest.raises(InvalidRerankResult, match="malformed"):
        search(system, ranking_provider=Malformed())
    with Session(system["engine"]) as db:
        assert db.scalar(select(ModelCall).where(ModelCall.operation == "rerank")).status == "failed"
        trace = db.scalar(select(RetrievalTrace))
        assert trace.status == "failed" and trace.results == []


def test_foreign_sources_never_reach_reranker(system):
    foreign = {
        **system,
        "workspace": system["foreign"],
        "users": {**system["users"], "admin": system["users"]["other"]},
    }
    add_version(foreign, b"# Private\nForbidden marker.")
    ingest(foreign)
    own = add_version(system)
    ingest(system)

    class Inspected(TestReranker):
        def score(self, query, passages):
            assert len(passages) == 1 and "Forbidden marker" not in passages[0]
            return super().score(query, passages)

    assert search(system, ranking_provider=Inspected())["results"][0]["version_id"] == str(own.id)


def test_internal_reranker_failure_is_not_reported_as_invalid_user_input(system, monkeypatch):
    def broken(*args, **kwargs):
        raise InvalidRerankResult("malformed scores")

    monkeypatch.setattr("app.modules.knowledge.retrieval.retrieve", broken)
    client = system["client"]
    response = client.post(
        f"/api/workspaces/{system['workspace']}/retrieval",
        headers=login(client, "viewer"),
        json={"query": "valid question", "limit": 5},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "Search scoring failed. Please retry."
