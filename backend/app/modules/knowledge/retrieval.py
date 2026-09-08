"""Exact PostgreSQL vector search with permission filters before candidate materialization."""

import time

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.knowledge.ingestion import SPACE, embeddings
from app.modules.knowledge.models import Chunk, Document, DocumentVersion
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.knowledge.splitting import lexical_terms
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.service import membership
from app.providers.recorded_embeddings import encode_recorded


def access(db, workspace_id, actor_id):
    # Membership, withdrawal and publication writers use the same workspace lock.
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    membership(db, workspace_id, actor_id)


def candidates(db, workspace_id, vector, query, limit):
    distance = Chunk.embedding.cosine_distance(vector)
    base = (
        select(Chunk, Document.title, DocumentVersion.checksum, distance.label("distance"))
        .join(
            Document,
            (Document.active_version_id == Chunk.version_id) & (Document.workspace_id == Chunk.workspace_id),
        )
        .join(DocumentVersion, DocumentVersion.id == Chunk.version_id)
        .where(
            Chunk.workspace_id == workspace_id, Document.withdrawn.is_(False), Chunk.embedding_space == SPACE
        )
    )
    semantic = list(db.execute(base.order_by(distance, Chunk.id).limit(20)))
    terms = lexical_terms(query)
    lexical = (
        list(
            db.execute(base.where(Chunk.lexical_terms.overlap(terms)).order_by(distance, Chunk.id).limit(20))
        )
        if terms
        else []
    )
    fused, rows = {}, {}
    for ranking in (semantic, lexical):
        for rank, row in enumerate(ranking, start=1):
            key = row[0].id
            rows[key] = row
            fused[key] = fused.get(key, 0) + 1 / (60 + rank)
    results = []
    for key in sorted(fused, key=lambda key: (-fused[key], str(key)))[:limit]:
        chunk, title, checksum, value = rows[key]
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
                "rank_score": fused[key],
            }
        )
    return results


def retrieve(engine, workspace_id, actor_id, query, limit=5, provider=None):
    query = query.strip()
    if not query or len(query) > 1000 or not 1 <= limit <= 10:
        raise HTTPException(422, "Use a query of 1–1000 characters and a limit of 1–10")
    started = time.monotonic()
    with Session(engine, expire_on_commit=False) as db, db.begin():
        access(db, workspace_id, actor_id)
        trace = RetrievalTrace(workspace_id=workspace_id, actor_id=actor_id, query=query)
        db.add(trace)
        db.flush()
        trace_id = trace.id
    try:
        batch = encode_recorded(
            engine,
            provider or embeddings(),
            workspace_id,
            actor_id,
            [query],
            "query",
            authorize=lambda db: access(db, workspace_id, actor_id),
            retrieval_id=trace_id,
        )
        with Session(engine) as db, db.begin():
            access(db, workspace_id, actor_id)
            results = candidates(db, workspace_id, batch.vectors[0], query, limit)
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
                "status": "candidates" if results else "no_sources",
                "results": results,
            }
    except Exception as error:
        with Session(engine) as db, db.begin():
            trace = db.get(RetrievalTrace, trace_id)
            trace.status = "failed"
            trace.error_code = type(error).__name__[:64]
            trace.duration_ms = round((time.monotonic() - started) * 1000, 2)
        raise
