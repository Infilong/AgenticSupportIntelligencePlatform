"""Separate administrative inspection from blind, single-pipeline request export."""

from fastapi import HTTPException
from sqlalchemy import select

from app.jobs.models import Job
from app.modules.comparisons import access, service
from app.modules.comparisons.models import Pipeline
from app.modules.support.context import digest
from app.modules.support.models import SupportRun
from app.modules.support.reading import export_handoff, visible_state
from app.modules.support.service import handoff_for


def export(db, workspace_id, actor_id, comparison_id, name):
    row = access.get(db, workspace_id, actor_id, comparison_id)
    item = service.pipeline(db, row, name)
    if item.run_id:
        handoff = export_handoff(db, workspace_id, actor_id, item.run_id)
        return {key: handoff[key] for key in ("generation_request", "request_hash", "context_hash")}
    if item.state != "waiting_for_input":
        raise HTTPException(409, "Pipeline is not waiting for generation")
    service.validate_request(db, row, item)
    return {
        "generation_request": item.request,
        "request_hash": item.request_hash,
        "context_hash": digest(item.context),
    }


def detail(db, workspace_id, actor_id, comparison_id):
    row = access.get(db, workspace_id, actor_id, comparison_id, active=False)
    items = []
    for item in db.scalars(
        select(Pipeline)
        .where(Pipeline.workspace_id == workspace_id, Pipeline.comparison_id == row.id)
        .order_by(Pipeline.name)
    ):
        job = db.get(Job, item.job_id)
        result = {
            "name": item.name,
            "configuration": item.configuration,
            "state": job.state if job.state in {"failed", "cancelled", "running"} else item.state,
            "error_code": job.error_code,
            "job_id": item.job_id,
            "attempts": job.attempts,
            "retrieval_id": item.retrieval_id,
            "run_id": item.run_id,
            "initial_response": item.response,
            "response_hash": item.response_hash,
            "request_hash": item.request_hash,
            "contributor_id": item.contributor_id,
            "reviewed_response": None,
        }
        if item.run_id:
            run = db.get(SupportRun, item.run_id)
            job = db.get(Job, run.job_id)
            handoff = handoff_for(db, run)
            result.update(
                state=visible_state(run, job),
                outcome=run.outcome,
                error_code=job.error_code,
                job_id=job.id,
                attempts=job.attempts,
                retrieval_id=run.retrieval_id,
                initial_response=handoff.response if handoff else None,
                response_hash=handoff.response_hash if handoff else None,
                request_hash=handoff.request_hash if handoff else None,
                contributor_id=handoff.contributor_id if handoff else None,
                reviewed_response=run.reviewed_response,
            )
        items.append(result)
    return {
        "id": row.id,
        "question": row.question,
        "language": row.language,
        "corpus_hash": row.corpus_hash,
        "cancelled": row.cancelled,
        "comparable": not row.cancelled and row.corpus_hash == digest(access.corpus(db, workspace_id)),
        "generation_quality": "not_verified",
        "pipelines": items,
    }
