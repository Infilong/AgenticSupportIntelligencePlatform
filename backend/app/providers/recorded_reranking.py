"""Record dispatch in the authorized snapshot transaction and inference outcome separately."""

import math
import time

from sqlalchemy.orm import Session

from app.modules.usage.models import ModelCall
from app.providers.local_reranker import MODEL, REVISION, InvalidRerankResult


def start_reranking(db, workspace_id, actor_id, retrieval_id):
    call = ModelCall(
        workspace_id=workspace_id,
        actor_id=actor_id,
        retrieval_id=retrieval_id,
        operation="rerank",
        provider="local_cpu",
        model=MODEL,
        revision=REVISION,
    )
    db.add(call)
    db.flush()
    return call.id


def score_recorded(engine, provider, call_id, query, passages, accounting_guard=None):
    started = time.monotonic()
    try:
        batch = provider.score(query, passages)
        if len(batch.scores) != len(passages) or any(not math.isfinite(v) for v in batch.scores):
            raise InvalidRerankResult("Reranker returned malformed scores")
    except Exception as error:
        with Session(engine) as db, db.begin():
            if accounting_guard:
                accounting_guard(db)
            call = db.get(ModelCall, call_id)
            call.status = "failed"
            call.error_code = type(error).__name__[:64]
            call.duration_ms = (time.monotonic() - started) * 1000
            call.api_cost_usd = 0
        raise
    with Session(engine) as db, db.begin():
        if accounting_guard:
            accounting_guard(db)
        call = db.get(ModelCall, call_id)
        call.status = "succeeded"
        call.input_tokens = batch.input_tokens
        call.duration_ms = batch.duration_ms
        call.api_cost_usd = 0
    return batch.scores
