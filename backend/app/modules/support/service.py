"""Atomic user commands; workspace lock serializes authority, idempotency and cancellation."""

import uuid

from fastapi import HTTPException
from sqlalchemy import func, select

from app.jobs.queue import JobCancelled, authorize, enqueue, owned, request_cancel
from app.modules.support.context import citations, digest, validate_sources
from app.modules.support.models import Handoff, Message, SupportRun
from app.modules.workspaces.service import membership


def get_run(db, workspace_id, run_id):
    run = db.scalar(
        select(SupportRun)
        .where(SupportRun.workspace_id == workspace_id, SupportRun.id == run_id)
        .with_for_update()
    )
    if run is None:
        raise HTTPException(404, "Processing attempt not found")
    return run


def handoff_for(db, run):
    return db.scalar(
        select(Handoff).where(Handoff.workspace_id == run.workspace_id, Handoff.run_id == run.id)
    )


def eligible(db, run, job=None):
    message = db.scalar(
        select(Message).where(Message.workspace_id == run.workspace_id, Message.id == run.message_id)
    )
    membership(db, run.workspace_id, message.actor_id, {"operator", "admin"})
    membership(db, run.workspace_id, run.creator_id, {"operator", "admin"})
    if run.state == "cancelled":
        raise JobCancelled()
    if job is not None:
        current = owned(db, job.id, job.lease_token)
        if run.job_id != job.id or current.cancel_requested:
            raise JobCancelled()
    handoff = handoff_for(db, run)
    if handoff is not None and handoff.contributor_id is not None:
        membership(db, run.workspace_id, handoff.contributor_id, {"admin"})
    return message


def create_message(db, workspace_id, actor_id, data, key):
    authorize(db, workspace_id, actor_id)
    value = digest({"actor": str(actor_id), **data.model_dump()})
    previous = db.scalar(
        select(Message).where(Message.workspace_id == workspace_id, Message.submission_key == key)
    )
    if previous:
        if previous.input_hash != value:
            raise HTTPException(409, "Submission key already belongs to different input")
        run = db.scalar(
            select(SupportRun)
            .where(SupportRun.workspace_id == workspace_id, SupportRun.message_id == previous.id)
            .order_by(SupportRun.attempt_number)
        )
        return {"message_id": previous.id, "run_id": run.id, "job_id": run.job_id}
    count = db.scalar(select(func.count()).select_from(Message).where(Message.workspace_id == workspace_id))
    if count >= 10000:
        raise HTTPException(409, "Workspace message limit reached")
    message = Message(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        actor_id=actor_id,
        original=data.original,
        language=data.language,
        submission_key=key,
        input_hash=value,
    )
    db.add(message)
    db.flush()
    run_id = uuid.uuid4()
    job = enqueue(
        db, workspace_id, actor_id, "support_run", f"support:{run_id}", {"run_id": str(run_id)}, priority=0
    )
    run = SupportRun(
        id=run_id,
        workspace_id=workspace_id,
        message_id=message.id,
        job_id=job.id,
        creator_id=actor_id,
        input_text=message.original,
    )
    db.add(run)
    db.flush()
    return {"message_id": message.id, "run_id": run.id, "job_id": job.id}


def submit_response(db, workspace_id, actor_id, run_id, handoff_id, data):
    authorize(db, workspace_id, actor_id)
    membership(db, workspace_id, actor_id, {"admin"})
    run = get_run(db, workspace_id, run_id)
    if run.state == "cancelled":
        raise HTTPException(409, "This processing attempt was cancelled")
    eligible(db, run)
    handoff = handoff_for(db, run)
    if handoff is None or handoff.id != handoff_id:
        raise HTTPException(404, "Development handoff not found")
    if data.context_hash != handoff.context_hash:
        raise HTTPException(409, "The response does not match this evidence context")
    response = data.model_dump(mode="json")
    response_hash = digest({"contributor": str(actor_id), "response": response})
    if handoff.response is not None:
        if handoff.response_hash != response_hash:
            raise HTTPException(409, "A different response has already been submitted")
        return run
    if run.state != "waiting_for_input":
        raise HTTPException(409, "This processing attempt is not waiting for a response")
    validate_sources(db, workspace_id, handoff.context)
    citations(handoff.context, response)
    handoff.response, handoff.response_hash = response, response_hash
    handoff.contributor_id = actor_id
    handoff.submitted_at = db.scalar(select(func.clock_timestamp()))
    job = enqueue(
        db, workspace_id, actor_id, "support_run", f"resume:{handoff.id}", {"run_id": str(run.id)}, priority=0
    )
    run.job_id, run.state = job.id, "queued"
    return run


def cancel_run(db, workspace_id, actor_id, run_id):
    authorize(db, workspace_id, actor_id)
    run = get_run(db, workspace_id, run_id)
    if run.state in {"completed", "rejected"}:
        raise HTTPException(409, "Processing has already finished")
    request_cancel(db, workspace_id, actor_id, run.job_id)
    run.state = "cancelled"
    run.finished_at = db.scalar(select(func.clock_timestamp()))
    return run
