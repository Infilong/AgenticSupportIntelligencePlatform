"""Exact PostgreSQL vector search with permission filters before candidate materialization."""

import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge.ingestion import embeddings
from app.modules.knowledge.models import Chunk, Document, DocumentVersion
from app.modules.knowledge.population import active_chunks
from app.modules.knowledge.recovery import RetrievalOwner, RetrievalOwnershipLost
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.service import membership
from app.providers.local_reranker import MAX_CANDIDATES, reranker
from app.providers.recorded_embeddings import encode_recorded
from app.providers.recorded_reranking import score_recorded, start_reranking


def access(db, workspace_id, actor_id):
    # Membership, withdrawal and publication writers use the same workspace lock.
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    membership(db, workspace_id, actor_id)


def candidates(db, workspace_id, vector):
    distance = Chunk.embedding.cosine_distance(vector)
    base = active_chunks(workspace_id).with_only_columns(
        Chunk, Document.title, DocumentVersion.checksum, distance.label("distance")
    )
    results = []
    for chunk, title, checksum, value in db.execute(base.order_by(distance, Chunk.id).limit(MAX_CANDIDATES)):
        results.append(
            {
                "chunk_id": str(chunk.id),
                "version_id": str(chunk.version_id),
                "document_id": str(
                    db.scalar(
                        select(DocumentVersion.document_id).where(
                            DocumentVersion.workspace_id == workspace_id,
                            DocumentVersion.id == chunk.version_id,
                        )
                    )
                ),
                "title": title,
                "section": chunk.section,
                "text": chunk.text,
                "start_offset": chunk.start_offset,
                "end_offset": chunk.end_offset,
                "checksum": checksum,
                "cosine_similarity": 1 - value,
                "rank_score": 1 - value,
            }
        )
    return results


def retrieve(
    engine,
    workspace_id,
    actor_id,
    query,
    limit=5,
    provider=None,
    ranking_provider=None,
    on_trace=None,
    execution_guard=None,
):
    query = query.strip()
    if not query or len(query) > 1000 or not 1 <= limit <= 10:
        raise HTTPException(422, "Use a query of 1–1000 characters and a limit of 1–10")
    with RetrievalOwner(engine) as owner:
        return _retrieve(
            engine,
            workspace_id,
            actor_id,
            query,
            limit,
            provider,
            ranking_provider,
            on_trace,
            execution_guard,
            owner,
        )


def _retrieve(
    engine, workspace_id, actor_id, query, limit, provider, ranking_provider, on_trace, execution_guard, owner
):
    started = time.monotonic()

    def check_access(db):
        access(db, workspace_id, actor_id)
        if execution_guard is not None:
            execution_guard(db)

    with Session(engine, expire_on_commit=False) as db, db.begin():
        check_access(db)
        trace = RetrievalTrace(id=owner.trace_id, workspace_id=workspace_id, actor_id=actor_id, query=query)
        db.add(trace)
        db.flush()
        trace_id = trace.id
        if on_trace is not None:
            on_trace(db, trace_id)
    try:
        batch = encode_recorded(
            engine,
            provider or embeddings(),
            workspace_id,
            actor_id,
            [query],
            "query",
            authorize=check_access,
            retrieval_id=trace_id,
            accounting_guard=owner.check,
        )
        with Session(engine) as db, db.begin():
            check_access(db)
            owner.check(db)
            snapshots = candidates(db, workspace_id, batch.vectors[0])
            call_id = start_reranking(db, workspace_id, actor_id, trace_id) if snapshots else None
        if snapshots:
            scores = score_recorded(
                engine,
                ranking_provider or reranker(),
                call_id,
                query,
                [row["text"] for row in snapshots],
                accounting_guard=owner.check,
            )
            for row, score in zip(snapshots, scores, strict=True):
                row["rank_score"] = score
        with Session(engine) as db, db.begin():
            check_access(db)
            owner.check(db)
            # Withdrawal/replacement may have completed while the local model was scoring.
            active = {
                str(value)
                for value in db.scalars(
                    select(Document.active_version_id).where(
                        Document.workspace_id == workspace_id,
                        Document.withdrawn.is_(False),
                        Document.active_version_id.is_not(None),
                        Document.id.in_([row["document_id"] for row in snapshots]),
                    )
                )
            }
            results = sorted(
                [row for row in snapshots if row["version_id"] in active],
                key=lambda row: (-row["rank_score"], row["chunk_id"]),
            )[:limit]
            trace = db.get(RetrievalTrace, trace_id)
            trace.status = "succeeded"
            # Keep identifiers/scores, not duplicate protected passages in the trace.
            trace.results = [
                {k: v for k, v in row.items() if k not in {"text", "title", "section"}} for row in results
            ]
            trace.duration_ms = round((time.monotonic() - started) * 1000, 2)
            return {
                "trace_id": trace_id,
                "duration_ms": trace.duration_ms,
                "status": "candidates" if results else ("sources_changed" if snapshots else "no_sources"),
                "results": results,
            }
    except RetrievalOwnershipLost:
        raise  # The sweep owns abandoned records; never overwrite uncertainty with a late exception.
    except Exception as error:
        with Session(engine) as db, db.begin():
            trace = owner.check(db)
            trace.status = "failed"
            trace.error_code = type(error).__name__[:64]
            trace.duration_ms = round((time.monotonic() - started) * 1000, 2)
        raise
