"""Validate human publication without preventing uncited human-authored safe responses."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import GraphStep, GraphStepStatus
from app.models.review import HumanReview, ReviewDecision
from app.services.action_review_gate import validate_action_reviews
from app.services.answer_citations import has_answer_citations
from app.services.graph_step_ordering import step_order
from app.services.review_transaction import HumanReviewInvalidDecisionError


def validate_review_answer(db: Session, review: HumanReview, decision: ReviewDecision,
                           edited_answer: str | None, reviewer=None) -> None:
    validate_action_reviews(db, review, decision, reviewer)
    if decision == ReviewDecision.rejected:
        return
    if decision not in {ReviewDecision.approved, ReviewDecision.edited}:
        raise HumanReviewInvalidDecisionError("Decision must resolve the review.")
    answer = review.proposed_answer if decision == ReviewDecision.approved else edited_answer
    if not answer or not answer.strip():
        message = ("Cannot approve a review without a proposed answer."
                   if decision == ReviewDecision.approved
                   else "Edited reviews require an edited answer.")
        raise HumanReviewInvalidDecisionError(message)
    if "#chunk-" not in answer.lower():
        return
    step = db.scalar(select(GraphStep).where(
        GraphStep.workspace_id == review.workspace_id,
        GraphStep.graph_run_id == review.graph_run_id,
        GraphStep.step_name == "compress_context",
    ).order_by(*step_order(descending=True)).limit(1))
    chunks = []
    if step is not None and step.status == GraphStepStatus.succeeded:
        try:
            output = json.loads(step.output_json)
        except (TypeError, json.JSONDecodeError):
            output = None
        if isinstance(output, dict):
            packed = output.get("packed_context_chunks")
            if isinstance(packed, list):
                chunks = [chunk for chunk in packed if isinstance(chunk, dict)]
    if not has_answer_citations({"draft_answer": answer, "packed_context_chunks": chunks}):
        raise HumanReviewInvalidDecisionError(
            "Answer citations must match this run's packed evidence. "
            "Correct the references, write a response without unsupported citations, or reject."
        )
