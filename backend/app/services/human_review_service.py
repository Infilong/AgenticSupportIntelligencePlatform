from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.agent import GraphRun
from app.models.review import HumanReview, ReviewDecision
from app.models.user import User
from app.services.review_answer_validation import validate_review_answer
from app.services.review_outcome import apply_review_decision
from app.services.review_transaction import (
    HumanReviewAlreadyResolvedError as HumanReviewAlreadyResolvedError,
)
from app.services.review_transaction import (
    HumanReviewAssignmentConflictError as HumanReviewAssignmentConflictError,
)
from app.services.review_transaction import (
    HumanReviewInvalidDecisionError as HumanReviewInvalidDecisionError,
)
from app.services.review_transaction import (
    HumanReviewNotFoundError as HumanReviewNotFoundError,
)
from app.services.review_transaction import (
    commit_review,
    pending_review,
)

CRITICAL_REVIEW_REASONS = (
    "prompt_injection",
    "privacy_complaint",
    "high_safety_risk",
    "model_provider_failure",
)
HIGH_REVIEW_REASONS = ("model_budget_failure", "unsupported_answer", "citation_required")
EVIDENCE_REVIEW_REASONS = ("unsupported_answer", "citation_required", "confidence_threshold")
MODEL_REVIEW_REASONS = ("model_provider_failure", "model_budget_failure")


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

    def list_reviews(
        self,
        *,
        workspace_id: UUID,
        decision: str = "all",
        queue_filter: str = "all",
        reviewer_id: UUID | None = None,
        search: str | None = None,
        sort: str = "severity",
        limit: int = 30,
        offset: int = 0,
    ) -> list[HumanReview]:
        filters = self._review_filters(
            workspace_id=workspace_id,
            decision=decision,
            queue_filter=queue_filter,
            reviewer_id=reviewer_id,
            search=search,
        )
        statement = (
            select(HumanReview)
            .join(GraphRun, HumanReview.graph_run_id == GraphRun.id)
            .where(*filters)
        )
        if sort == "oldest":
            statement = statement.order_by(HumanReview.created_at.asc())
        elif sort == "severity":
            statement = statement.order_by(
                _review_severity_rank().desc(), HumanReview.created_at.desc()
            )
        else:
            statement = statement.order_by(HumanReview.created_at.desc())

        return list(
            self.db.scalars(statement.offset(max(offset, 0)).limit(max(min(limit, 100), 1))).all()
        )

    def count_reviews(
        self,
        *,
        workspace_id: UUID,
        decision: str = "all",
        queue_filter: str = "all",
        reviewer_id: UUID | None = None,
        search: str | None = None,
    ) -> int:
        filters = self._review_filters(
            workspace_id=workspace_id,
            decision=decision,
            queue_filter=queue_filter,
            reviewer_id=reviewer_id,
            search=search,
        )
        total = self.db.scalar(
            select(func.count(HumanReview.id))
            .join(GraphRun, HumanReview.graph_run_id == GraphRun.id)
            .where(*filters)
        )
        return int(total or 0)

    def _review_filters(
        self,
        *,
        workspace_id: UUID,
        decision: str,
        queue_filter: str,
        reviewer_id: UUID | None,
        search: str | None,
    ) -> list:
        filters = [HumanReview.workspace_id == workspace_id]
        if decision == "pending":
            filters.append(HumanReview.reviewer_decision == ReviewDecision.pending)
        elif decision == "resolved":
            filters.append(HumanReview.reviewer_decision != ReviewDecision.pending)

        filters.extend(_queue_filter_conditions(queue_filter=queue_filter, reviewer_id=reviewer_id))
        search_term = (search or "").strip()
        if search_term:
            filters.append(_review_search_condition(search_term))
        return filters

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

    def claim(self, *, workspace_id: UUID, review_id: UUID, reviewer: User) -> HumanReview:
        review = pending_review(
            self.db, workspace_id=workspace_id, review_id=review_id, reviewer=reviewer
        )
        review.reviewer_id = reviewer.id
        return commit_review(self.db, review=review, reviewer=reviewer, action="claimed")

    def release(self, *, workspace_id: UUID, review_id: UUID, reviewer: User) -> HumanReview:
        review = pending_review(
            self.db, workspace_id=workspace_id, review_id=review_id, reviewer=reviewer
        )
        review.reviewer_id = None
        return commit_review(self.db, review=review, reviewer=reviewer, action="released")

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
        review = pending_review(
            self.db, workspace_id=workspace_id, review_id=review_id, reviewer=reviewer
        )
        validate_review_answer(self.db, review, decision, edited_answer, reviewer)
        review.reviewer_id = reviewer.id
        review.reviewer_decision = decision
        review.edited_answer = edited_answer
        review.comments = comments
        review.resolved_at = datetime.now(UTC)
        apply_review_decision(self.db, review=review, reviewer=reviewer)
        return commit_review(self.db, review=review, reviewer=reviewer, action="resolved")

def _reason_contains_any(reasons: tuple[str, ...]):
    return or_(*[HumanReview.reason.ilike(f"%{reason}%") for reason in reasons])


def _queue_filter_conditions(*, queue_filter: str, reviewer_id: UUID | None) -> list:
    if queue_filter == "mine":
        if reviewer_id is None:
            return [HumanReview.reviewer_id.is_(None), HumanReview.reviewer_id.is_not(None)]
        return [HumanReview.reviewer_id == reviewer_id]
    if queue_filter == "unassigned":
        return [HumanReview.reviewer_id.is_(None)]
    if queue_filter == "critical":
        return [_reason_contains_any(CRITICAL_REVIEW_REASONS)]
    if queue_filter == "evidence":
        return [_reason_contains_any(EVIDENCE_REVIEW_REASONS)]
    if queue_filter == "model":
        return [_reason_contains_any(MODEL_REVIEW_REASONS)]
    if queue_filter == "language":
        return [HumanReview.reason.ilike("%language_preservation%")]
    return []


def _review_search_condition(search_term: str):
    pattern = f"%{search_term}%"
    return or_(
        cast(HumanReview.id, String).ilike(pattern),
        cast(HumanReview.graph_run_id, String).ilike(pattern),
        HumanReview.reason.ilike(pattern),
        cast(HumanReview.reviewer_decision, String).ilike(pattern),
        HumanReview.proposed_answer.ilike(pattern),
        HumanReview.edited_answer.ilike(pattern),
        HumanReview.comments.ilike(pattern),
        GraphRun.input_message.ilike(pattern),
        cast(GraphRun.language, String).ilike(pattern),
        cast(GraphRun.status, String).ilike(pattern),
        GraphRun.route_decision.ilike(pattern),
        GraphRun.final_answer.ilike(pattern),
    )


def _review_severity_rank():
    return case(
        (_reason_contains_any(CRITICAL_REVIEW_REASONS), 3),
        (_reason_contains_any(HIGH_REVIEW_REASONS), 2),
        else_=1,
    )
