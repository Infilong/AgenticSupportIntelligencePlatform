from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.review import ReviewDecision


class HumanReviewRunContext(BaseModel):
    graph_run_id: UUID
    input_message: str
    language: str | None
    status: str
    route_decision: str | None
    final_answer: str | None
    created_at: datetime
    completed_at: datetime | None


class HumanReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    graph_run_id: UUID
    reviewer_id: UUID | None
    reviewer_display_name: str | None = None
    reviewer_email: str | None = None
    reason: str
    proposed_answer: str | None
    reviewer_decision: ReviewDecision
    edited_answer: str | None
    comments: str | None
    created_at: datetime
    resolved_at: datetime | None
    run: HumanReviewRunContext | None = None
    review_context: dict[str, Any] | None = None


class HumanReviewListResponse(BaseModel):
    items: list[HumanReviewResponse]
    total: int
    limit: int
    offset: int
    has_next: bool


class HumanReviewResolveRequest(BaseModel):
    decision: ReviewDecision
    edited_answer: str | None = Field(default=None, max_length=4000)
    comments: str | None = Field(default=None, max_length=2000)

    @field_validator("decision")
    @classmethod
    def decision_must_be_terminal(cls, value: ReviewDecision) -> ReviewDecision:
        if value == ReviewDecision.pending:
            raise ValueError("decision must resolve the review")
        return value

    @field_validator("edited_answer", "comments")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
