"""Atomic admission and cancellation; baseline contributions never become support drafts."""

import uuid

from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import func, select

from app.core.settings import GenerationSettings
from app.jobs.queue import authorize, enqueue, request_cancel
from app.modules.comparisons import access
from app.modules.comparisons.models import Comparison, Pipeline
from app.modules.support.context import citations, digest, validate_sources
from app.modules.support.models import SupportRun
from app.modules.support.schemas import CitationInput, DevelopmentResponse
from app.modules.support.service import cancel_run, create_message, handoff_for, submit_response
from app.modules.workspaces.service import membership
from app.providers.development_generation import render

STRATEGIES = {"direct_llm": None, "vector_rag": "vector", "hybrid_rag": "hybrid", "system_v1": "hybrid"}


class Response(DevelopmentResponse):
    request_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    citations: list[CitationInput] = Field(default_factory=list, max_length=5)


def create(db, workspace_id, actor_id, data, key):
    authorize(db, workspace_id, actor_id)
    membership(db, workspace_id, actor_id, {"admin"})
    input_data = data.model_dump()
    if input_data.get("generation_mode") == "manual":
        input_data.pop("generation_mode")
    identity = digest({"actor": str(actor_id), **input_data})
    previous = db.scalar(
        select(Comparison).where(Comparison.workspace_id == workspace_id, Comparison.submission_key == key)
    )
    if previous is not None:
        if previous.input_hash != identity:
            raise HTTPException(409, "Submission key belongs to different input")
        return previous.id
    count = db.scalar(
        select(func.count()).select_from(Comparison).where(Comparison.workspace_id == workspace_id)
    )
    if count >= 1000:
        raise HTTPException(409, "Workspace comparison limit reached")
    snapshot = access.corpus(db, workspace_id)
    local = getattr(data, "generation_mode", "manual") == "local_ollama"
    settings = GenerationSettings()
    if local and settings.generation_mode != "local_ollama":
        raise HTTPException(409, "Local generation is not enabled")
    row = Comparison(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        actor_id=actor_id,
        submission_key=key,
        input_hash=identity,
        question=data.original,
        language=data.language,
        corpus=snapshot,
        corpus_hash=digest(snapshot),
    )
    db.add(row)
    db.flush()
    for name, strategy in STRATEGIES.items():
        pipeline_id = uuid.uuid4()
        if name == "system_v1":
            result = create_message(db, workspace_id, actor_id, data, f"comparison:{row.id}")
            job_id, run_id = result["job_id"], result["run_id"]
        else:
            job_id = enqueue(
                db,
                workspace_id,
                actor_id,
                "comparison_prepare",
                f"comparison:{pipeline_id}",
                {"pipeline_id": str(pipeline_id)},
                priority=0,
            ).id
            run_id = None
        db.add(
            Pipeline(
                id=pipeline_id,
                workspace_id=workspace_id,
                comparison_id=row.id,
                name=name,
                job_id=job_id,
                run_id=run_id,
                configuration={
                    "strategy": strategy,
                    "limit": 5,
                    "context_bytes": 24000,
                    "transport": "local_ollama" if local else "attributed_development",
                    "version": 2 if local else 1,
                    **({"model": settings.ollama_model, "endpoint": settings.ollama_url} if local else {}),
                },
            )
        )
    db.flush()
    return row.id


def pipeline(db, row, name):
    result = db.scalar(
        select(Pipeline)
        .where(
            Pipeline.workspace_id == row.workspace_id, Pipeline.comparison_id == row.id, Pipeline.name == name
        )
        .with_for_update()
    )
    if result is None:
        raise HTTPException(404, "Pipeline not found")
    return result


def validate_request(db, row, item):
    if (
        item.context is None
        or item.request != render(item.context)
        or item.request_hash != digest(item.request)
    ):
        raise HTTPException(409, "Generation request is unavailable or changed")
    validate_sources(db, row.workspace_id, item.context)


def submit(db, workspace_id, actor_id, comparison_id, name, data):
    row = access.get(db, workspace_id, actor_id, comparison_id)
    item = pipeline(db, row, name)
    if item.configuration["transport"] == "local_ollama":
        raise HTTPException(409, "Local comparisons do not accept human generation contributions")
    if item.run_id:
        if not data.citations:
            raise HTTPException(422, "A cited system draft needs at least one source")
        run = db.get(SupportRun, item.run_id)
        handoff = handoff_for(db, run)
        if handoff is None:
            raise HTTPException(409, "System pipeline is not waiting for generation")
        submit_response(
            db,
            workspace_id,
            actor_id,
            run.id,
            handoff.id,
            DevelopmentResponse.model_validate(data.model_dump()),
        )
        return
    validate_request(db, row, item)
    if data.request_hash != item.request_hash or data.context_hash != digest(item.context):
        raise HTTPException(409, "Response does not match the generation request")
    response = data.model_dump(mode="json")
    if name == "direct_llm":
        if data.citations:
            raise HTTPException(422, "Direct baseline cannot cite retrieved evidence")
    else:
        citations(item.context, response)
    identity = digest({"contributor": str(actor_id), "response": response})
    if item.response is not None:
        if item.response_hash != identity:
            raise HTTPException(409, "A different contribution already exists")
        return
    if item.state != "waiting_for_input":
        raise HTTPException(409, "Pipeline is not waiting for generation")
    item.response, item.response_hash = response, identity
    item.contributor_id, item.state = actor_id, "completed"
    item.submitted_at = db.scalar(select(func.clock_timestamp()))


def cancel(db, workspace_id, actor_id, comparison_id):
    row = access.get(db, workspace_id, actor_id, comparison_id, active=False)
    for item in db.scalars(
        select(Pipeline).where(Pipeline.workspace_id == workspace_id, Pipeline.comparison_id == row.id)
    ):
        if item.run_id:
            run = db.get(SupportRun, item.run_id)
            if run.state not in {"completed", "rejected", "cancelled"}:
                cancel_run(db, workspace_id, actor_id, run.id)
        else:
            request_cancel(db, workspace_id, actor_id, item.job_id)
            if item.state in {"queued", "waiting_for_input"}:
                item.state = "cancelled"
    row.cancelled = True
