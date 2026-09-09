"""Local administrative registration; no report upload or mutation HTTP endpoint."""

import hashlib
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.evaluations.models import EvaluationRecord
from app.modules.evaluations.projection import project
from app.modules.identity.models import User
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.service import membership


def register(db, raw: bytes, actor_id: UUID):
    workspace_id, snapshot, references = project(raw)
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
    if workspace is None:
        raise HTTPException(404, "Workspace not found")
    membership(db, workspace_id, actor_id, {"admin"})
    if db.get(User, actor_id) is None:
        raise HTTPException(404, "Administrator not found")
    digest = hashlib.sha256(raw).hexdigest()
    existing = db.scalar(
        select(EvaluationRecord).where(
            EvaluationRecord.workspace_id == workspace_id,
            EvaluationRecord.report_sha256 == digest,
        )
    )
    if existing is not None:
        return existing
    ids = {trace.id for trace, _, _ in references}
    if len(ids) != len(references):
        raise ValueError("Every measured request needs a distinct trace")
    rows = {
        row.id: row
        for row in db.scalars(
            select(RetrievalTrace).where(
                RetrievalTrace.workspace_id == workspace_id,
                RetrievalTrace.id.in_(ids),
            )
        )
    }
    for trace, question, strategy in references:
        stored = rows.get(trace.id)
        expected = "cosine20-mmarco-rerank-v2" if strategy == "vector_rerank" else strategy + "-v1"
        if (
            stored is None
            or stored.query != question
            or trace.query != question
            or (stored.status != "succeeded" or trace.strategy != expected or stored.strategy != expected)
        ):
            raise ValueError("Report trace is unavailable, mismatched or outside the primary workspace")
    record = EvaluationRecord(
        workspace_id=workspace_id,
        registered_by=actor_id,
        report_sha256=digest,
        source_commit=snapshot.source_commit,
        snapshot=snapshot.model_dump(mode="json"),
    )
    db.add(record)
    db.flush()
    return record
