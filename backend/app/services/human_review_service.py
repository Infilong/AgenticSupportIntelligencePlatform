from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.agent import Checkpoint, GraphRun, GraphRunStatus
from app.models.review import HumanReview, ReviewDecision
from app.models.user import User

CRITICAL_REVIEW_REASONS = (
    "prompt_injection",
    "privacy_complaint",
    "high_safety_risk",
    "model_provider_failure",
)
HIGH_REVIEW_REASONS = ("model_budget_failure", "unsupported_answer", "citation_required")
EVIDENCE_REVIEW_REASONS = ("unsupported_answer", "citation_required", "confidence_threshold")
MODEL_REVIEW_REASONS = ("model_provider_failure", "model_budget_failure")


class HumanReviewNotFoundError(ValueError):
    pass


class HumanReviewAlreadyResolvedError(ValueError):
    pass


class HumanReviewInvalidDecisionError(ValueError):
    pass


class HumanReviewAssignmentConflictError(ValueError):
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
        review = self.get_review(workspace_id=workspace_id, review_id=review_id)
        if review.reviewer_decision != ReviewDecision.pending:
            raise HumanReviewAlreadyResolvedError("Human review was already resolved.")
        if review.reviewer_id is not None and review.reviewer_id != reviewer.id:
            raise HumanReviewAssignmentConflictError(
                "Human review is assigned to another reviewer."
            )
        review.reviewer_id = reviewer.id
        self.db.commit()
        self.db.refresh(review)
        return review

    def release(self, *, workspace_id: UUID, review_id: UUID, reviewer: User) -> HumanReview:
        review = self.get_review(workspace_id=workspace_id, review_id=review_id)
        if review.reviewer_decision != ReviewDecision.pending:
            raise HumanReviewAlreadyResolvedError("Human review was already resolved.")
        if review.reviewer_id is not None and review.reviewer_id != reviewer.id:
            raise HumanReviewAssignmentConflictError(
                "Human review is assigned to another reviewer."
            )
        review.reviewer_id = None
        self.db.commit()
        self.db.refresh(review)
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
        if review.reviewer_id is not None and review.reviewer_id != reviewer.id:
            raise HumanReviewAssignmentConflictError(
                "Human review is assigned to another reviewer."
            )
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
