"""Shared authority and corpus fences, including the linked support workflow."""

from fastapi import HTTPException
from sqlalchemy import select

from app.jobs.queue import authorize
from app.modules.comparisons.models import Comparison, Pipeline
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.support.context import digest
from app.modules.workspaces.service import membership


def corpus(db, workspace_id):
    rows = db.execute(
        select(Document.id, DocumentVersion.id, DocumentVersion.checksum)
        .join(
            DocumentVersion,
            (DocumentVersion.id == Document.active_version_id)
            & (DocumentVersion.workspace_id == Document.workspace_id),
        )
        .where(Document.workspace_id == workspace_id, Document.withdrawn.is_(False))
        .order_by(Document.id)
    )
    return [[str(document), str(version), checksum] for document, version, checksum in rows]


def get(db, workspace_id, actor_id, comparison_id, active=True):
    authorize(db, workspace_id, actor_id)
    membership(db, workspace_id, actor_id, {"admin"})
    row = db.scalar(
        select(Comparison)
        .where(Comparison.workspace_id == workspace_id, Comparison.id == comparison_id)
        .with_for_update()
    )
    if row is None:
        raise HTTPException(404, "Comparison not found")
    if active:
        membership(db, workspace_id, row.actor_id, {"admin"})
        if row.cancelled:
            raise HTTPException(409, "Comparison was cancelled")
        if digest(corpus(db, workspace_id)) != row.corpus_hash:
            raise HTTPException(409, "Knowledge changed; create a new comparison")
    return row


def linked(db, workspace_id, run_id):
    return db.scalar(select(Pipeline).where(Pipeline.workspace_id == workspace_id, Pipeline.run_id == run_id))


def support_guard(db, run):
    pipeline = linked(db, run.workspace_id, run.id)
    if pipeline is not None:
        get(db, run.workspace_id, run.creator_id, pipeline.comparison_id)
    return pipeline
