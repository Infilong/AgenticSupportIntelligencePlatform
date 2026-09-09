"""Versioned human-review continuation, independent of completed generation checkpoints."""

import time
import uuid
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.reviews.service import decision_for, draft_identity, reviewer_authority, validate_approval
from app.modules.support.models import RunStep
from app.workflows.checkpoints import locked_graph
from app.workflows.support_graph import guard


class ReviewState(TypedDict, total=False):
    draft_hash: str
    action: str
    response: str | None
    decision_id: str


def checked_decision(db, job, run_id, identity):
    run, _ = guard(db, job, run_id)
    decision = decision_for(db, run)
    if decision is None or decision.draft_hash != identity or decision.revision + 1 != run.review_version:
        raise ValueError("A matching stored review decision is required")
    if draft_identity(run.draft, run.citations) != identity:
        raise ValueError("The reviewed draft identity changed")
    reviewer_authority(db, run, decision.actor_id, decision.action)
    if decision.action != "reject":
        validate_approval(db, run)
    return run, decision


def execute(engine, job, identity, resume=False):
    run_id = uuid.UUID(job.payload["run_id"])

    def review(state):
        with Session(engine) as db, db.begin():
            guard(db, job, run_id)
        interrupt({"reason": "human_review", "draft_hash": state["draft_hash"]})
        with Session(engine) as db, db.begin():
            run, decision = checked_decision(db, job, run_id, state["draft_hash"])
            response = (
                None
                if decision.action == "reject"
                else decision.response
                if decision.action == "edit"
                else run.draft
            )
            return {"action": decision.action, "response": response, "decision_id": str(decision.id)}

    builder = StateGraph(ReviewState)
    builder.add_node("human_review", review)
    builder.add_edge(START, "human_review")
    builder.add_edge("human_review", END)
    config = {"configurable": {"thread_id": f"review-v1:{job.workspace_id}:{run_id}"}}
    with locked_graph(engine, run_id) as checkpointer:
        with Session(engine, expire_on_commit=False) as db, db.begin():
            guard(db, job, run_id)
            if resume:
                checked_decision(db, job, run_id, identity)
            db.execute(
                update(RunStep)
                .where(
                    RunStep.job_id == job.id, RunStep.job_attempt < job.attempts, RunStep.status == "started"
                )
                .values(status="uncertain", error_code="previous_attempt_interrupted")
            )
            step = RunStep(
                workspace_id=job.workspace_id,
                run_id=run_id,
                job_id=job.id,
                job_attempt=job.attempts,
                node="human_review",
            )
            db.add(step)
            db.flush()
            step_id = step.id
        started, status, error = time.monotonic(), "waiting", None
        try:
            graph = builder.compile(checkpointer=checkpointer)
            saved = graph.get_state(config)
            if not saved.values:
                graph.invoke({"draft_hash": identity}, config, durability="sync")
                saved = graph.get_state(config)
            if saved.values["draft_hash"] != identity:
                raise ValueError("Review checkpoint belongs to a different draft")
            failed_task = any(task.error is not None for task in saved.tasks)
            if resume and (saved.next or saved.interrupts or failed_task):
                if any(i.value.get("reason") != "human_review" for i in saved.interrupts):
                    raise ValueError("Expected a human-review interrupt")
                request = Command(resume=True) if saved.interrupts and not failed_task else None
                graph.invoke(request, config, durability="sync")
                saved = graph.get_state(config)
                # Retrying a failed node can recreate its interrupt. The durable decision
                # still owns this continuation; revalidate it before supplying the resume.
                if saved.interrupts:
                    if any(i.value.get("reason") != "human_review" for i in saved.interrupts):
                        raise ValueError("Expected a human-review interrupt")
                    with Session(engine) as db, db.begin():
                        checked_decision(db, job, run_id, identity)
                    graph.invoke(Command(resume=True), config, durability="sync")
                    saved = graph.get_state(config)
            with Session(engine) as db, db.begin():
                guard(db, job, run_id)
            pending = saved.next or saved.interrupts or any(task.error is not None for task in saved.tasks)
            if resume and (pending or not saved.values.get("decision_id") or not saved.values.get("action")):
                raise ValueError("Review continuation did not complete")
            status = "succeeded" if not pending and saved.values.get("decision_id") else "waiting"
            return saved.values
        except Exception as exc:
            status, error = "failed", type(exc).__name__[:64]
            raise
        finally:
            with Session(engine) as db, db.begin():
                step = db.get(RunStep, step_id)
                step.status, step.error_code = status, error
                step.duration_ms = round((time.monotonic() - started) * 1000, 2)
