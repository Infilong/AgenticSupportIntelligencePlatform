"""Reauthorize trace reads and resolve only workspace-owned source identities."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.knowledge.models import Chunk, Document, DocumentVersion
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.workspaces.service import membership


def read_trace(db, workspace_id, trace_id, actor_id):
    membership(db, workspace_id, actor_id)
    trace = db.scalar(
        select(RetrievalTrace).where(
            RetrievalTrace.workspace_id == workspace_id,
            RetrievalTrace.id == trace_id,
        )
    )
    if trace is None:
        raise HTTPException(404, "Retrieval record not found")
    stage = trace.stages or {}
    recorded = stage.get("candidates", [])[:40]
    ids = [UUID(row["chunk_id"]) for row in recorded]
    rows = (
        db.execute(
            select(Chunk, Document)
            .join(
                DocumentVersion,
                DocumentVersion.id == Chunk.version_id,
            )
            .join(Document, Document.id == DocumentVersion.document_id)
            .where(
                Chunk.workspace_id == workspace_id,
                DocumentVersion.workspace_id == workspace_id,
                Document.workspace_id == workspace_id,
                Chunk.id.in_(ids),
            )
        )
        if ids
        else []
    )
    sources = {str(chunk.id): (chunk, document) for chunk, document in rows}
    candidates = []
    for item in recorded:
        source = sources.get(item["chunk_id"])
        if source is None:
            continue
        chunk, document = source
        candidates.append(
            {
                **item,
                "document_id": document.id,
                "version_id": chunk.version_id,
                "title": document.title,
                "section": chunk.section,
                "start_offset": chunk.start_offset,
                "currently_active": not document.withdrawn and document.active_version_id == chunk.version_id,
            }
        )
    return {
        "id": trace.id,
        "query": trace.query,
        "status": trace.status,
        "strategy": trace.strategy,
        "duration_ms": trace.duration_ms,
        "error_code": trace.error_code,
        "trace_version": stage.get("version"),
        "phase": stage.get("phase", "unavailable"),
        "candidate_queries_ms": stage.get("candidate_queries_ms"),
        "parameters": stage.get("parameters", {}),
        "candidates": candidates,
    }
