from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Checkpoint, GraphRun, GraphRunStatus
from app.models.review import HumanReview, ReviewDecision
from app.models.user import User


class HumanReviewNotFoundError(ValueError):
    pass


class HumanReviewAlreadyResolvedError(ValueError):
    pass


class HumanReviewInvalidDecisionError(ValueError):
    pass


class HumanReviewService:
    def __init__(self, db: Session):
        self.db = db

    def create_pending(
        self,
        *,
        workspace_id: UUID,
        graph_run_id: UUID,
        reason: str,
        proposed_answer: str | None,
    ) -> HumanReview:
        review = HumanReview(
            workspace_id=workspace_id,
            graph_run_id=graph_run_id,
            reason=reason,
            proposed_answer=proposed_answer,
            reviewer_decision=ReviewDecision.pending,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def list_reviews(self, *, workspace_id: UUID) -> list[HumanReview]:
        return list(
            self.db.scalars(
                select(HumanReview)
                .where(HumanReview.workspace_id == workspace_id)
                .order_by(HumanReview.created_at.desc())
            ).all()
        )

    def get_review(self, *, workspace_id: UUID, review_id: UUID) -> HumanReview:
        review = self.db.scalar(
            select(HumanReview).where(
                HumanReview.workspace_id == workspace_id,
                HumanReview.id == review_id,
            )
        )
        if review is None:
            raise HumanReviewNotFoundError("Human review was not found.")
        return review

    def resolve(
        self,
        *,
        workspace_id: UUID,
        review_id: UUID,
        reviewer: User,
        decision: ReviewDecision,
        edited_answer: str | None,
        comments: str | None,
    ) -> HumanReview:
        review = self.get_review(workspace_id=workspace_id, review_id=review_id)
        if review.reviewer_decision != ReviewDecision.pending:
            raise HumanReviewAlreadyResolvedError("Human review was already resolved.")
        if decision == ReviewDecision.approved and not review.proposed_answer:
            raise HumanReviewInvalidDecisionError(
                "Cannot approve a review without a proposed answer."
            )
        if decision == ReviewDecision.edited and not edited_answer:
            raise HumanReviewInvalidDecisionError("Edited reviews require an edited answer.")
        review.reviewer_id = reviewer.id
        review.reviewer_decision = decision
        review.edited_answer = edited_answer
        review.comments = comments
        review.resolved_at = datetime.now(UTC)
        self._apply_review_decision_to_run(review=review, reviewer=reviewer)
        self.db.commit()
        self.db.refresh(review)
        return review

    def _apply_review_decision_to_run(self, *, review: HumanReview, reviewer: User) -> None:
        run = self.db.scalar(
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
            run.status = GraphRunStatus.failed
            run.route_decision = "human_rejected"
            run.final_answer = None
        run.completed_at = review.resolved_at
        self.db.add(
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
