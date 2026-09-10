"""Review commands bind a single attributed decision to an immutable draft."""

from fastapi import HTTPException
from sqlalchemy import select

from app.jobs.queue import authorize, enqueue
from app.modules.reviews.models import ReviewDecision
from app.modules.support.context import digest, validate_sources
from app.modules.support.service import eligible, get_run, handoff_for
from app.modules.workspaces.service import membership


def draft_identity(draft, citations):
    return digest({"draft": draft, "citations": citations})


def decision_for(db, run):
    return db.scalar(
        select(ReviewDecision).where(
            ReviewDecision.workspace_id == run.workspace_id, ReviewDecision.run_id == run.id
        )
    )


def reviewer_authority(db, run, actor_id, action):
    roles = (
        {"admin"}
        if run.review_kind in {"policy_exception", "unclassified"} and action in {"approve", "edit"}
        else {"operator", "admin"}
    )
    membership(db, run.workspace_id, actor_id, roles)


def validate_approval(db, run):
    handoff = handoff_for(db, run)
    if handoff is None or handoff.response is None:
        raise HTTPException(409, "This run has no attributable development draft")
    if handoff.provider == "local_ollama":
        from app.modules.support.local_response import snapshot

        snapshot(db, handoff)
    validate_sources(db, run.workspace_id, handoff.context)


def decision_response(run, decision):
    if decision.action == "reject":
        return None
    if decision.action == "approve":
        return run.draft
    if decision.action in {"edit", "clarify"} and decision.response and decision.response.strip():
        return decision.response
    raise ValueError("Stored review decision has no valid response")


def submit(db, workspace_id, actor_id, run_id, data):
    authorize(db, workspace_id, actor_id)
    run = get_run(db, workspace_id, run_id)
    reviewer_authority(db, run, actor_id, data.action)
    payload_hash = digest({"actor": str(actor_id), **data.model_dump(mode="json")})
    previous = decision_for(db, run)
    if previous:
        if previous.payload_hash != payload_hash:
            raise HTTPException(409, "This draft already has a different review decision")
        return run
    if run.state != "awaiting_review":
        raise HTTPException(409, "This run is not awaiting review")
    eligible(db, run)
    if data.expected_revision != run.review_version or data.draft_hash != draft_identity(
        run.draft, run.citations
    ):
        raise HTTPException(409, "The draft changed; reload before reviewing")
    if data.action in {"approve", "edit"}:
        validate_approval(db, run)
    decision = ReviewDecision(
        workspace_id=workspace_id,
        run_id=run.id,
        actor_id=actor_id,
        revision=run.review_version,
        draft_hash=data.draft_hash,
        payload_hash=payload_hash,
        action=data.action,
        reason=data.reason,
        response=data.response if data.action in {"edit", "clarify"} else None,
    )
    db.add(decision)
    job = enqueue(
        db,
        workspace_id,
        actor_id,
        "support_review",
        f"review:{run.id}:{run.review_version}",
        {"run_id": str(run.id)},
        priority=0,
    )
    run.review_version += 1
    run.job_id, run.state = job.id, "queued"
    db.flush()
    return run
