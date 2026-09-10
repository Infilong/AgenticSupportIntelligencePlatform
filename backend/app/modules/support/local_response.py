"""Persist local inference identity separately from human development contributions."""

import time
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.modules.support.context import citations, digest, validate_sources
from app.modules.support.models import Handoff
from app.modules.support.service import handoff_for
from app.modules.usage.models import ModelCall
from app.providers.local_generation import generate, request_for


def snapshot(db, handoff):
    request, response = handoff.generation_request, handoff.response
    if (
        handoff.provider != "local_ollama"
        or handoff.contributor_id is not None
        or not request
        or not response
        or digest(request) != handoff.request_hash
        or digest(handoff.context) != handoff.context_hash
        or digest({"request_hash": handoff.request_hash, "response": response}) != handoff.response_hash
    ):
        raise HTTPException(409, "Local generation evidence is incomplete or changed")
    call = db.get(ModelCall, uuid.UUID(request["call_id"]))
    if (
        call is None
        or call.workspace_id != handoff.workspace_id
        or call.provider != "local_ollama"
        or call.status != "succeeded"
        or call.model != request["model"]
        or call.revision != handoff.request_hash
    ):
        raise HTTPException(409, "Local generation ledger does not match the response")
    validate_sources(db, handoff.workspace_id, handoff.context)
    if response["citations"]:
        citations(handoff.context, response)
    return response


def execute(engine, job, state, guard, inference=None):
    inference = inference or generate
    with Session(engine, expire_on_commit=False) as db, db.begin():
        run, _ = guard(db)
        validate_sources(db, job.workspace_id, state["context"])
        handoff = handoff_for(db, run)
        if handoff is not None:
            if handoff.context_hash != state["context_hash"]:
                raise ValueError("Local generation context changed")
            if handoff.response is not None:
                return snapshot(db, handoff)
            # A crashed/failed dispatch must not silently create another model call.
            raise ValueError("Local generation outcome unavailable; start a fresh attempt")
        request = request_for(state["context"], state["generation_model"], state["generation_endpoint"])
        call_id = uuid.uuid4()
        request["call_id"] = str(call_id)
        request_hash = digest(request)
        call = ModelCall(
            id=call_id,
            workspace_id=job.workspace_id,
            actor_id=run.creator_id,
            job_id=job.id,
            job_attempt=job.attempts,
            retrieval_id=uuid.UUID(state["retrieval_id"]),
            operation="generate",
            provider="local_ollama",
            model=request["model"],
            revision=request_hash,
        )
        handoff = Handoff(
            workspace_id=job.workspace_id,
            run_id=run.id,
            provider="local_ollama",
            context=state["context"],
            context_hash=state["context_hash"],
            prompt_version=state["context"]["prompt_version"],
            generation_request=request,
            request_hash=request_hash,
        )
        db.add_all([call, handoff])
        db.flush()
        handoff_id = handoff.id
    started = time.monotonic()
    try:
        response, usage = inference(request, state["context"])
        if state.get("routing_version") and not response.get("routing"):
            response = {
                **response,
                "routing": {
                    "version": state["routing_version"],
                    "decision": "review" if response["citations"] else "missing",
                    "reason": "The model did not provide a complete routing decision; human input is needed.",
                },
            }
        if response["citations"]:
            citations(state["context"], response)
    except Exception as error:
        with Session(engine) as db, db.begin():
            db.execute(
                update(ModelCall)
                .where(ModelCall.id == call_id, ModelCall.status == "started")
                .values(
                    status="failed",
                    error_code=type(error).__name__[:64],
                    duration_ms=(time.monotonic() - started) * 1000,
                    api_cost_usd=0,
                )
            )
        raise
    # Record actual compute even if cancellation/revocation prevents domain publication.
    with Session(engine) as db, db.begin():
        changed = db.execute(
            update(ModelCall)
            .where(ModelCall.id == call_id, ModelCall.status == "started")
            .values(
                status="succeeded",
                input_tokens=usage.get("input_tokens"),
                duration_ms=(time.monotonic() - started) * 1000,
                api_cost_usd=0,
            )
        ).rowcount
        if changed != 1:
            raise ValueError("Local generation dispatch was reconciled; start a fresh attempt")
    with Session(engine) as db, db.begin():
        guard(db)
        validate_sources(db, job.workspace_id, state["context"])
        handoff = db.get(Handoff, handoff_id)
        response = {**response, "usage": usage}
        handoff.response = response
        handoff.response_hash = digest({"request_hash": request_hash, "response": response})
        handoff.submitted_at = db.scalar(select(func.clock_timestamp()))
    return response
