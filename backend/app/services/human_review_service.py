from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.review import HumanReview, ReviewDecision
from app.models.user import User


class HumanReviewNotFoundError(ValueError):
    pass


class HumanReviewAlreadyResolvedError(ValueError):
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
        review.reviewer_id = reviewer.id
        review.reviewer_decision = decision
        review.edited_answer = edited_answer
        review.comments = comments
        review.resolved_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(review)
        return review
