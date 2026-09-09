import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge.lexical import LexicalQueryTooLong
from app.modules.knowledge.models import Chunk
from app.modules.knowledge.retrieval import retrieve
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.knowledge.service import set_withdrawn
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import change_member
from tests.integration.conftest import login
from tests.integration.test_bm25 import seed_chunks
from tests.integration.test_knowledge import TestEmbeddings
from tests.integration.test_retrieval import TestReranker


class Forbidden:
    def encode_batch(self, *_):
        raise AssertionError("Unexpected embedding call")

    def score(self, *_):
        raise AssertionError("Unexpected reranking call")


def search(system, strategy, **kwargs):
    return retrieve(
        system["engine"],
        system["workspace"],
        system["users"]["viewer"].id,
        kwargs.pop("query", "refund"),
        strategy=strategy,
        provider=kwargs.pop("provider", TestEmbeddings() if strategy != "bm25" else Forbidden()),
        ranking_provider=kwargs.pop(
            "ranking_provider", TestReranker() if strategy.endswith("rerank") else Forbidden()
        ),
        **kwargs,
    )


@pytest.mark.parametrize("strategy", ["vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank"])
def test_strategies_record_only_executed_stages_and_provider_work(system, strategy):
    own, _ = seed_chunks(system, ["refund policy", "refund refund"])
    foreign, _ = seed_chunks(system, ["refund " * 100], workspace=system["foreign"])
    result = search(system, strategy)
    assert {row["chunk_id"] for row in result["results"]} == set(own)
    assert all(row["cosine_similarity"] is None for row in result["results"]) == (strategy == "bm25")
    with Session(system["engine"]) as db:
        trace = db.get(RetrievalTrace, result["trace_id"])
        assert trace.stages["phase"] == "completed"
        candidates = trace.stages["candidates"]
        assert {row["chunk_id"] for row in candidates} == set(own)
        assert not set(foreign) & {row["chunk_id"] for row in candidates}
        for row in candidates:
            assert ("vector_rank" in row) == (strategy != "bm25")
            assert ("bm25_rank" in row) == (strategy in {"bm25", "hybrid", "hybrid_rerank"})
            assert ("fusion_rank" in row) == strategy.startswith("hybrid")
            assert ("reranker_rank" in row) == strategy.endswith("rerank")
            assert row["final_rank"] in {1, 2} and row["exclusion"] is None
            assert "text" not in row
        calls = set(db.scalars(select(ModelCall.operation).where(ModelCall.retrieval_id == trace.id)))
        expected = set() if strategy == "bm25" else {"embed_query"}
        if strategy.endswith("rerank"):
            expected.add("rerank")
        assert calls == expected


def test_disjoint_branch_union_cutoff_missing_scores_and_revalidation(system):
    vector_ids, _ = seed_chunks(system, ["semantic" for _ in range(20)])
    lexical_ids, lexical_doc = seed_chunks(system, ["refund" for _ in range(20)])
    with Session(system["engine"]) as db, db.begin():
        for chunk in db.scalars(select(Chunk).where(Chunk.id.in_([uuid.UUID(x) for x in lexical_ids]))):
            chunk.embedding = [0.0, 1.0] + [0.0] * 382

    class Changed(TestReranker):
        def score(self, query, passages):
            assert len(passages) == 20
            with Session(system["engine"]) as db, db.begin():
                set_withdrawn(db, system["workspace"], system["users"]["admin"].id, lexical_doc, True)
            return super().score(query, passages)

    result = search(system, "hybrid_rerank", ranking_provider=Changed())
    assert all(row["chunk_id"] in vector_ids for row in result["results"])
    with Session(system["engine"]) as db:
        rows = db.get(RetrievalTrace, result["trace_id"]).stages["candidates"]
        assert len(rows) == 40 and sum(row["selected_for_reranker"] for row in rows) == 20
        for row in rows:
            lexical = row["chunk_id"] in lexical_ids
            assert ("cosine_similarity" not in row) == lexical
            assert ("bm25_score" in row) == lexical
            if lexical:
                assert row["exclusion"] == "source_changed" and row["final_rank"] is None
            elif not row["selected_for_reranker"]:
                assert row["exclusion"] == "fusion_cutoff"


def test_failed_reranking_preserves_candidates_without_invented_final_scores(system):
    ids, _ = seed_chunks(system, ["refund"])

    class Broken(TestReranker):
        def score(self, *_):
            raise OSError("synthetic failure")

    with pytest.raises(OSError):
        search(system, "hybrid_rerank", ranking_provider=Broken())
    with Session(system["engine"]) as db:
        trace = db.scalar(select(RetrievalTrace))
        assert trace.status == "failed" and trace.error_code == "OSError"
        assert trace.stages["phase"] == "candidates"
        assert trace.stages["candidates"][0]["chunk_id"] == ids[0]
        assert "reranker_score" not in trace.stages["candidates"][0]
        assert "final_rank" not in trace.stages["candidates"][0]


@pytest.mark.parametrize("strategy", ["bm25", "hybrid", "hybrid_rerank"])
def test_lexical_query_bound_precedes_all_provider_work(system, strategy):
    query = " ".join(f"t{i}" for i in range(129))
    assert len(query) < 1000
    with pytest.raises(LexicalQueryTooLong):
        search(system, strategy, query=query, provider=Forbidden())
    with Session(system["engine"]) as db:
        assert list(db.scalars(select(ModelCall))) == []
        trace = db.scalar(select(RetrievalTrace))
        assert trace.status == "failed" and trace.error_code == "LexicalQueryTooLong"
        assert trace.stages["phase"] == "started"


def test_trace_http_permissions_legacy_and_bm25_empty_input(system):
    ids, _ = seed_chunks(system, ["refund"])
    client = system["client"]
    headers = login(client, "viewer")
    path = f"/api/workspaces/{system['workspace']}/retrieval"
    response = client.post(path, headers=headers, json={"query": "refund", "strategy": "bm25"})
    assert response.status_code == 200, response.text
    trace_id = response.json()["trace_id"]
    detail = client.get(f"{path}/{trace_id}")
    assert detail.status_code == 200
    row = detail.json()["candidates"][0]
    assert row["chunk_id"] == ids[0] and row["cosine_similarity"] is None
    assert client.get(f"/api/workspaces/{system['foreign']}/retrieval/{trace_id}").status_code == 404
    assert (
        client.post(path, headers=headers, json={"query": "!!!", "strategy": "bm25"}).json()["status"]
        == "no_matches"
    )
    assert (
        client.post(path, headers=headers, json={"query": "refund", "strategy": "madeup"}).status_code == 422
    )
    with Session(system["engine"]) as db, db.begin():
        db.get(RetrievalTrace, uuid.UUID(trace_id)).stages = {}
    legacy = client.get(f"{path}/{trace_id}").json()
    assert legacy["phase"] == "unavailable" and legacy["candidates"] == []
    with Session(system["engine"]) as db:
        change_member(
            db, system["workspace"], system["users"]["admin"].id, system["users"]["viewer"].id, None
        )
    assert client.get(f"{path}/{trace_id}").status_code == 404
