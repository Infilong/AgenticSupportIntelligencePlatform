"""Bounded in-memory staging; vectors and active version publish in one fenced transaction."""

import uuid
from functools import lru_cache

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.jobs.contracts import Publication
from app.jobs.queue import JobCancelled, owned
from app.modules.knowledge.models import Chunk, DocumentVersion
from app.modules.knowledge.service import admin_scope, get_document
from app.modules.knowledge.splitting import lexical_terms, split_document
from app.providers.local_embeddings import MODEL, REVISION, LocalEmbeddings
from app.providers.recorded_embeddings import encode_recorded

SPACE = f"{MODEL}:{REVISION}:normalized-query-passage-v1"


@lru_cache(maxsize=1)
def embeddings():
    return LocalEmbeddings(Settings().embedding_cache)


def check_active(db, job, document_id, version_id):
    admin_scope(db, job.workspace_id, job.actor_id)
    document = get_document(db, job.workspace_id, document_id, lock=True)
    active_job = owned(db, job.id, job.lease_token)
    if active_job.cancel_requested or document.withdrawn or document.desired_version_id != version_id:
        raise JobCancelled()
    return document


def index_document(engine, job, provider=None):
    version_id = uuid.UUID(job.payload["version_id"])
    with Session(engine) as db, db.begin():
        version = db.scalar(
            select(DocumentVersion).where(
                DocumentVersion.workspace_id == job.workspace_id,
                DocumentVersion.id == version_id,
                DocumentVersion.job_id == job.id,
            )
        )
        if version is None:
            raise ValueError("Job does not reference its own workspace document version")
        document_id, source = version.document_id, version.text
        check_active(db, job, document_id, version_id)
    provider = provider or embeddings()

    def checkpoint():
        with Session(engine) as db, db.begin():
            check_active(db, job, document_id, version_id)

    passages = split_document(source, provider, checkpoint)
    staged = []
    for start in range(0, len(passages), 16):
        selected = passages[start : start + 16]
        batch = encode_recorded(
            engine,
            provider,
            job.workspace_id,
            job.actor_id,
            [passage.text for passage in selected],
            "passage",
            job_id=job.id,
            job_attempt=job.attempts,
            authorize=lambda db: check_active(db, job, document_id, version_id),
        )
        if len(batch.vectors) != len(selected):
            raise ValueError("Embedding result count does not match the input batch")
        staged.extend(zip(selected, batch.vectors, strict=True))

    def publish(db, current_job):
        document = check_active(db, current_job, document_id, version_id)
        count = db.scalar(
            select(func.count()).select_from(Chunk).where(Chunk.workspace_id == job.workspace_id)
        )
        if count + len(staged) > 50000:
            raise ValueError("Workspace retained chunk limit reached")
        for ordinal, (passage, vector) in enumerate(staged):
            db.add(
                Chunk(
                    workspace_id=job.workspace_id,
                    version_id=version_id,
                    ordinal=ordinal,
                    text=passage.text,
                    start_offset=passage.start,
                    end_offset=passage.end,
                    section=passage.section,
                    token_count=passage.token_count,
                    embedding=vector,
                    embedding_space=SPACE,
                    lexical_terms=lexical_terms(passage.text),
                )
            )
        db.flush()
        db.get(DocumentVersion, version_id).indexed_at = db.scalar(select(func.clock_timestamp()))
        document.active_version_id = version_id
        db.flush()
        return {"document_id": str(document_id), "version_id": str(version_id), "chunks": len(staged)}

    return Publication(publish)
