import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.contracts import Publication
from app.modules.reviews.service import draft_identity
from app.workflows.review_graph import checked_decision, execute
from app.workflows.support_graph import guard


def process(engine, job):
    run_id = uuid.UUID(job.payload["run_id"])
    with Session(engine) as db, db.begin():
        run, _ = guard(db, job, run_id)
        identity = draft_identity(run.draft, run.citations)
    result = execute(engine, job, identity, resume=True)

    def publish(db, current):
        run, decision = checked_decision(db, current, run_id, identity)
        if result.get("decision_id") != str(decision.id) or result.get("action") != decision.action:
            raise ValueError("Completed review checkpoint does not match the stored decision")
        expected = (
            None
            if decision.action == "reject"
            else decision.response
            if decision.action == "edit"
            else run.draft
        )
        if result.get("response") != expected:
            raise ValueError("Reviewed response differs from the attributed decision")
        run.reviewed_response = result["response"]
        run.state = "rejected" if decision.action == "reject" else "completed"
        run.outcome = "rejected_response" if decision.action == "reject" else "approved_response"
        run.finished_at = db.scalar(select(func.clock_timestamp()))
        return {"run_id": str(run.id), "state": run.state, "outcome": run.outcome}

    return Publication(publish)
