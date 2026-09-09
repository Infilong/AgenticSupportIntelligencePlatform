"""Workspace-authorized read projections; raw graph state is never exposed."""

from fastapi import HTTPException
from sqlalchemy import func, select

from app.jobs.models import Job
from app.jobs.queue import authorize
from app.modules.reviews.service import decision_for, draft_identity
from app.modules.support.context import validate_sources
from app.modules.support.models import Message, RunStep, SupportRun
from app.modules.support.service import eligible, get_run, handoff_for
from app.modules.usage.models import ModelCall
from app.modules.workspaces.service import membership


def visible_state(run, job):
    if run.state == "queued":
        return job.state
    return run.state


def handoff_timing(handoff):
    if handoff.submitted_at is None:
        return {"handoff_elapsed_ms": None, "timing_status": "pending"}
    elapsed = (handoff.submitted_at - handoff.created_at).total_seconds() * 1000
    if elapsed < 0:
        return {"handoff_elapsed_ms": None, "timing_status": "clock_anomaly"}
    return {"handoff_elapsed_ms": elapsed, "timing_status": "recorded"}


def messages(db, workspace_id, actor_id, search, offset, limit):
    membership(db, workspace_id, actor_id)
    filters = [Message.workspace_id == workspace_id, Message.original.icontains(search, autoescape=True)]
    total = db.scalar(select(func.count()).select_from(Message).where(*filters))
    rows = db.execute(
        select(Message, SupportRun, Job)
        .join(
            SupportRun,
            (SupportRun.message_id == Message.id) & (SupportRun.workspace_id == Message.workspace_id),
        )
        .join(Job, Job.id == SupportRun.job_id)
        .where(*filters)
        .order_by(Message.created_at.desc(), Message.id)
        .offset(offset)
        .limit(limit)
    )
    return {
        "items": [
            {
                "id": m.id,
                "original": m.original,
                "language": m.language,
                "created_at": m.created_at,
                "run_id": r.id,
                "state": visible_state(r, j),
                "outcome": r.outcome,
                "error_code": j.error_code,
            }
            for m, r, j in rows
        ],
        "total": total,
    }


def detail(db, workspace_id, actor_id, run_id):
    membership(db, workspace_id, actor_id)
    run = db.scalar(
        select(SupportRun).where(SupportRun.workspace_id == workspace_id, SupportRun.id == run_id)
    )
    if run is None:
        raise HTTPException(404, "Processing attempt not found")
    message = db.get(Message, run.message_id)
    job = db.get(Job, run.job_id)
    handoff = handoff_for(db, run)
    decision = decision_for(db, run)
    steps = db.scalars(
        select(RunStep)
        .where(RunStep.workspace_id == workspace_id, RunStep.run_id == run_id)
        .order_by(RunStep.created_at, RunStep.id)
        .limit(100)
    )
    calls = []
    if run.retrieval_id:
        calls = list(
            db.scalars(
                select(ModelCall)
                .where(ModelCall.workspace_id == workspace_id, ModelCall.retrieval_id == run.retrieval_id)
                .order_by(ModelCall.created_at)
                .limit(50)
            )
        )
    return {
        "id": run.id,
        "message_id": message.id,
        "original": message.original,
        "language": message.language,
        "state": visible_state(run, job),
        "outcome": run.outcome,
        "review_kind": run.review_kind,
        "review_version": run.review_version,
        "draft_hash": draft_identity(run.draft, run.citations) if run.draft and run.citations else None,
        "reviewed_response": run.reviewed_response,
        "review": {
            "id": decision.id,
            "actor_id": decision.actor_id,
            "action": decision.action,
            "reason": decision.reason,
            "response": decision.response,
            "revision": decision.revision,
            "created_at": decision.created_at,
        }
        if decision
        else None,
        "job_id": job.id,
        "error_code": job.error_code,
        "draft": run.draft,
        "citations": run.citations,
        "retrieval_id": run.retrieval_id,
        "handoff": {
            "id": str(handoff.id),
            "context_hash": handoff.context_hash,
            "provider": handoff.provider,
            "prompt_version": handoff.prompt_version,
            "created_at": handoff.created_at.isoformat(),
            "submitted_at": handoff.submitted_at.isoformat() if handoff.submitted_at else None,
            "contributor_id": str(handoff.contributor_id) if handoff.contributor_id else None,
            **handoff_timing(handoff),
        }
        if handoff
        else None,
        "steps": [
            {
                "id": str(s.id),
                "node": s.node,
                "status": s.status,
                "duration_ms": s.duration_ms,
                "job_attempt": s.job_attempt,
                "error_code": s.error_code,
            }
            for s in steps
        ],
        "model_calls": [
            {
                "id": str(c.id),
                "operation": c.operation,
                "provider": c.provider,
                "model": c.model,
                "revision": c.revision,
                "status": c.status,
                "input_tokens": c.input_tokens,
                "duration_ms": c.duration_ms,
                "api_cost_usd": c.api_cost_usd,
                "error_code": c.error_code,
            }
            for c in calls
        ],
    }


def export_handoff(db, workspace_id, actor_id, run_id):
    authorize(db, workspace_id, actor_id)
    membership(db, workspace_id, actor_id, {"admin"})
    run = get_run(db, workspace_id, run_id)
    if run.state != "waiting_for_input":
        raise HTTPException(409, "This processing attempt is not waiting for a response")
    eligible(db, run)
    handoff = handoff_for(db, run)
    if handoff is None:
        raise HTTPException(404, "Development handoff not found")
    validate_sources(db, workspace_id, handoff.context)
    return {
        "id": str(handoff.id),
        "context_hash": handoff.context_hash,
        "context": handoff.context,
        "provider": handoff.provider,
        "prompt_version": handoff.prompt_version,
    }
