"""Persist each application embedding attempt before dispatch and retain explicit failures."""

import time

from sqlalchemy.orm import Session

from app.modules.usage.models import ModelCall
from app.providers.local_embeddings import MODEL, REVISION


def encode_recorded(
    engine,
    provider,
    workspace_id,
    actor_id,
    texts,
    kind,
    job_id=None,
    job_attempt=None,
    authorize=None,
    retrieval_id=None,
):
    with Session(engine, expire_on_commit=False) as db, db.begin():
        if authorize:
            authorize(db)
        call = ModelCall(
            workspace_id=workspace_id,
            actor_id=actor_id,
            job_id=job_id,
            job_attempt=job_attempt,
            retrieval_id=retrieval_id,
            operation="embed_" + kind,
            provider="local_cpu",
            model=MODEL,
            revision=REVISION,
        )
        db.add(call)
        db.flush()
        call_id = call.id
    started = time.monotonic()
    try:
        batch = provider.encode_batch(texts, kind)
    except Exception as error:
        with Session(engine) as db, db.begin():
            row = db.get(ModelCall, call_id)
            row.status = "failed"
            row.error_code = type(error).__name__[:64]
            row.duration_ms = (time.monotonic() - started) * 1000
            row.api_cost_usd = 0.0  # Local compute; no external API dispatch.
        raise
    with Session(engine) as db, db.begin():
        row = db.get(ModelCall, call_id)
        row.status = "succeeded"
        row.input_tokens = batch.input_tokens
        row.duration_ms = batch.duration_ms
        row.api_cost_usd = batch.api_cost_usd
    return batch
