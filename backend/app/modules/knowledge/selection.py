"""Candidate collection and source snapshots; caller owns authorization/transaction fencing."""

import time
import uuid

from app.modules.knowledge import bm25
from app.modules.knowledge.fusion import RRF_K, fuse
from app.modules.knowledge.lexical import LEXICAL_VERSION
from app.modules.knowledge.models import Chunk, Document, DocumentVersion
from app.modules.knowledge.population import active_chunks

STRATEGIES = {"vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank"}
DEFAULT_STRATEGY = "vector_rerank"
TRACE_VERSION = "candidate-trace-v1"


def trace_start(strategy):
    return {
        "version": TRACE_VERSION,
        "strategy": strategy,
        "phase": "started",
        "candidates": [],
        "parameters": {
            "branch_limit": 20,
            "reranker_limit": 20,
            "rrf_k": RRF_K,
            "bm25_k1": bm25.K1,
            "bm25_b": bm25.B,
            "lexical_recipe": LEXICAL_VERSION,
        },
    }


def vector_candidates(db, workspace_id, vector):
    distance = Chunk.embedding.cosine_distance(vector)
    query = active_chunks(workspace_id).with_only_columns(Chunk.id, distance.label("distance"))
    return [
        {"chunk_id": str(row.id), "cosine_similarity": 1 - row.distance, "vector_rank": rank}
        for rank, row in enumerate(db.execute(query.order_by(distance, Chunk.id).limit(20)), 1)
    ]


def collect(db, workspace_id, query, vector, strategy):
    started = time.monotonic()
    vector_rows = vector_candidates(db, workspace_id, vector) if strategy != "bm25" else []
    lexical_rows = (
        bm25.candidates(db, workspace_id, query) if strategy in {"bm25", "hybrid", "hybrid_rerank"} else []
    )
    if strategy.startswith("hybrid"):
        ranked, score_key = fuse(vector_rows, lexical_rows), "fusion_score"
    elif strategy == "bm25":
        ranked, score_key = lexical_rows, "bm25_score"
    else:
        ranked, score_key = vector_rows, "cosine_similarity"
    chosen = {row["chunk_id"] for row in ranked[:20]}
    ids = [uuid.UUID(row["chunk_id"]) for row in ranked]
    source_query = (
        active_chunks(workspace_id)
        .with_only_columns(Chunk, Document.id.label("document_id"), Document.title, DocumentVersion.checksum)
        .where(Chunk.id.in_(ids))
    )
    sources = {str(row.Chunk.id): row for row in db.execute(source_query)} if ids else {}
    snapshots, candidates = [], []
    for row in ranked:
        source = sources[row["chunk_id"]]
        chunk = source.Chunk
        candidates.append(
            {
                **row,
                "document_id": str(source.document_id),
                "version_id": str(chunk.version_id),
                "selected_for_reranker": row["chunk_id"] in chosen and strategy.endswith("rerank"),
                "exclusion": None if row["chunk_id"] in chosen else "fusion_cutoff",
            }
        )
        if row["chunk_id"] in chosen:
            snapshots.append(
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": str(source.document_id),
                    "version_id": str(chunk.version_id),
                    "title": source.title,
                    "section": chunk.section,
                    "text": chunk.text,
                    "start_offset": chunk.start_offset,
                    "end_offset": chunk.end_offset,
                    "checksum": source.checksum,
                    "cosine_similarity": row.get("cosine_similarity"),
                    "rank_score": row[score_key],
                }
            )
    has_sources = (
        bool(ranked)
        or db.scalar(active_chunks(workspace_id).with_only_columns(Chunk.id).limit(1)) is not None
    )
    stage = {
        **trace_start(strategy),
        "phase": "candidates",
        "candidates": candidates,
        "candidate_queries_ms": round((time.monotonic() - started) * 1000, 2),
    }
    return snapshots, stage, has_sources


def finish(stage, snapshots, results, active_versions):
    scored = sorted(snapshots, key=lambda row: (-row["rank_score"], row["chunk_id"]))
    ranks = {row["chunk_id"]: index for index, row in enumerate(scored, 1)}
    scores = {row["chunk_id"]: row["rank_score"] for row in snapshots}
    final = {row["chunk_id"]: index for index, row in enumerate(results, 1)}
    candidates = []
    for item in stage["candidates"]:
        row = dict(item)
        key = row["chunk_id"]
        if row["selected_for_reranker"]:
            row.update(reranker_rank=ranks[key], reranker_score=scores[key])
        row["final_rank"] = final.get(key)
        if row["version_id"] not in active_versions:
            row["exclusion"] = "source_changed"
        elif key in scores and key not in final:
            row["exclusion"] = "final_cutoff"
        candidates.append(row)
    return {**stage, "phase": "completed", "candidates": candidates}
