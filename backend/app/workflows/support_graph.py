"""Real durable LangGraph with an explicitly attributed development-generation pause."""

import time
import uuid
from typing import TypedDict

from langgraph.errors import GraphInterrupt
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.jobs.queue import authorize
from app.modules.knowledge.retrieval import retrieve
from app.modules.support.context import digest, pack, validate_sources
from app.modules.support.models import RunStep, SupportRun
from app.modules.support.service import eligible, get_run, handoff_for
from app.providers.development_generation import replay, snapshot
from app.workflows.checkpoints import locked_graph


class State(TypedDict, total=False):
    original: str
    latest_input: str
    language: str
    outcome: str
    retrieval_id: str
    context: dict
    context_hash: str
    response: dict


CLARIFICATION = {
    "en": "Could you describe your question or the issue you need help with?",
    "ja": "ご質問やお困りの内容をもう少し詳しく教えてください。",
    "zh": "请进一步描述您的问题或需要帮助的事项。",
}


def guard(db, job, run_id):
    authorize(db, job.workspace_id, job.actor_id)
    run = get_run(db, job.workspace_id, run_id)
    message = eligible(db, run, job)
    return run, message


def execute(engine, job, retrieval=retrieve):
    run_id = uuid.UUID(job.payload["run_id"])

    def checkpoint():
        with Session(engine) as db, db.begin():
            guard(db, job, run_id)
            db.execute(
                update(RunStep)
                .where(
                    RunStep.workspace_id == job.workspace_id,
                    RunStep.run_id == run_id,
                    RunStep.job_id == job.id,
                    RunStep.job_attempt < job.attempts,
                    RunStep.status == "started",
                )
                .values(status="uncertain", error_code="previous_attempt_interrupted")
            )

    def traced(name, operation):
        def node(state):
            checkpoint()
            with Session(engine, expire_on_commit=False) as db, db.begin():
                step = RunStep(
                    workspace_id=job.workspace_id,
                    run_id=run_id,
                    job_id=job.id,
                    job_attempt=job.attempts,
                    node=name,
                )
                db.add(step)
                db.flush()
                step_id = step.id
            started, status, error = time.monotonic(), "succeeded", None
            try:
                result = operation(state)
                checkpoint()
                return result
            except GraphInterrupt:
                status = "waiting"
                raise
            except Exception as exc:
                status, error = "failed", type(exc).__name__[:64]
                raise
            finally:
                with Session(engine) as db, db.begin():
                    step = db.get(RunStep, step_id)
                    step.status, step.error_code = status, error
                    step.duration_ms = round((time.monotonic() - started) * 1000, 2)

        return node

    def validate(state):
        meaningful = sum(c.isalnum() for c in state.get("latest_input", state["original"])) >= 2
        return {"outcome": "retrieve" if meaningful else "clarification"}

    def search(state):
        with Session(engine) as db, db.begin():
            run, _ = guard(db, job, run_id)
            actor_id = run.creator_id

        def associate(db, trace_id):
            run, _ = guard(db, job, run_id)
            run.retrieval_id = trace_id

        result = retrieval(
            engine,
            job.workspace_id,
            actor_id,
            state["original"],
            limit=5,
            on_trace=associate,
            execution_guard=lambda db: guard(db, job, run_id),
        )
        context = pack(state["original"], state["language"], result["results"])
        return {
            "retrieval_id": str(result["trace_id"]),
            "context": context,
            "context_hash": digest(context),
            "outcome": "generate" if context["sources"] else "insufficient_evidence",
        }

    def generate(state):
        # No external call occurs here. Resume reads only the authenticated stored contribution.
        interrupt({"reason": "development_generation", "context_hash": state["context_hash"]})
        with Session(engine) as db, db.begin():
            run, _ = guard(db, job, run_id)
            handoff = handoff_for(db, run)
            if handoff is None or handoff.response is None or handoff.context_hash != state["context_hash"]:
                raise ValueError("A matching stored development response is required")
            validate_sources(db, job.workspace_id, handoff.context)
            record = snapshot(handoff)
        response = replay.invoke(record)
        return {"response": response, "outcome": "draft"}

    builder = StateGraph(State)
    builder.add_node("validate_input", traced("validate_input", validate))
    builder.add_node("retrieve_evidence", traced("retrieve_evidence", search))
    builder.add_node("development_generation", traced("development_generation", generate))
    builder.add_edge(START, "validate_input")
    builder.add_conditional_edges(
        "validate_input", lambda s: s["outcome"], {"retrieve": "retrieve_evidence", "clarification": END}
    )
    builder.add_conditional_edges(
        "retrieve_evidence",
        lambda s: s["outcome"],
        {"generate": "development_generation", "insufficient_evidence": END},
    )
    builder.add_edge("development_generation", END)
    config = {"configurable": {"thread_id": f"support:{job.workspace_id}:{run_id}"}}
    checkpoint()
    with locked_graph(engine, run_id) as checkpointer:
        checkpoint()
        graph = builder.compile(checkpointer=checkpointer)
        saved = graph.get_state(config)
        with Session(engine) as db, db.begin():
            run, message = guard(db, job, run_id)
            handoff = handoff_for(db, run)
            submitted = handoff is not None and handoff.response is not None
            latest_details = db.scalar(
                select(SupportRun.clarification)
                .where(
                    SupportRun.workspace_id == run.workspace_id,
                    SupportRun.message_id == run.message_id,
                    SupportRun.attempt_number <= run.attempt_number,
                    SupportRun.clarification.is_not(None),
                )
                .order_by(SupportRun.attempt_number.desc())
                .limit(1)
            )
            initial = {
                "original": run.input_text,
                "language": message.language,
                "latest_input": latest_details if latest_details is not None else message.original,
            }
        failed_task = any(task.error is not None for task in saved.tasks)
        if saved.values and not (saved.next or saved.interrupts or failed_task):
            return saved.values  # Completed checkpoint, domain publication may still need replay.
        if saved.values:
            if saved.interrupts and not submitted:
                return saved.values
            request = Command(resume=True) if saved.interrupts and not failed_task else None
        else:
            request = initial
        result = graph.invoke(request, config, durability="sync")
        recovered = graph.get_state(config)
        if submitted and recovered.interrupts:
            if any(i.value.get("reason") != "development_generation" for i in recovered.interrupts):
                raise ValueError("Expected a development-generation interrupt")
            checkpoint()
            result = graph.invoke(Command(resume=True), config, durability="sync")
        return result
