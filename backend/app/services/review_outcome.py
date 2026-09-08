"""Persist reviewed outcomes, preserving legacy status semantics."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Checkpoint, GraphRun, GraphRunStatus
from app.models.review import HumanReview, ReviewDecision
from app.models.task import TaskExecution
from app.models.user import User


def apply_review_decision(db: Session, *, review: HumanReview, reviewer: User) -> None:
    run = db.scalar(
        select(GraphRun).where(
            GraphRun.workspace_id == review.workspace_id,
            GraphRun.id == review.graph_run_id,
        )
    )
    if run is None:
        return
    final_answer = _final_answer_for_review(review)
    if review.reviewer_decision in {ReviewDecision.approved, ReviewDecision.edited}:
        run.status = GraphRunStatus.completed
        run.route_decision = f"human_{review.reviewer_decision.value}"
        run.final_answer = final_answer
    else:
        run.status = (GraphRunStatus.rejected if db.get(TaskExecution, run.id)
                      else GraphRunStatus.failed)
        run.route_decision = "human_rejected"
        run.final_answer = None
    run.completed_at = review.resolved_at
    db.add(
        Checkpoint(
            workspace_id=review.workspace_id,
            graph_run_id=review.graph_run_id,
            checkpoint_key=f"human_review_{review.reviewer_decision.value}:after",
            state_json=json.dumps(
                _review_checkpoint_state(review=review, run=run, reviewer=reviewer),
                ensure_ascii=False,
                default=str,
            ),
        )
    )



def _final_answer_for_review(review: HumanReview) -> str | None:
    if review.reviewer_decision == ReviewDecision.approved:
        return review.proposed_answer
    if review.reviewer_decision == ReviewDecision.edited:
        return review.edited_answer
    return None


def _review_checkpoint_state(*, review: HumanReview, run: GraphRun, reviewer: User) -> dict:
    return {
        "input_message": run.input_message,
        "detected_language": run.language,
        "route_decision": run.route_decision,
        "final_answer": run.final_answer,
        "human_review": {
            "review_id": str(review.id),
            "reviewer_id": str(reviewer.id),
            "decision": review.reviewer_decision.value,
            "reason": review.reason,
            "comments": review.comments,
        },
        "checkpoint": {
            "completed_step": f"human_review_{review.reviewer_decision.value}",
            "status": "succeeded" if run.status == GraphRunStatus.completed else "failed",
            "error_message": None,
            "state_keys": [
                "input_message",
                "detected_language",
                "route_decision",
                "final_answer",
                "human_review",
            ],
            "retrieved_chunk_count": 0,
            "citation_count": 0,
            "has_draft_answer": bool(review.proposed_answer),
            "has_final_answer": bool(run.final_answer),
        },
    }


