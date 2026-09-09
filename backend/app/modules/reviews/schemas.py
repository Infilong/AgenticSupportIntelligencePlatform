from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "edit", "reject", "clarify"]
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=0)
    draft_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    response: str | None = Field(default=None, max_length=8000)

    @model_validator(mode="after")
    def valid_text(self):
        if not self.reason.strip() or "\x00" in self.reason:
            raise ValueError("Provide a review reason without NUL characters")
        if self.action in {"edit", "clarify"}:
            if not self.response or not self.response.strip() or "\x00" in self.response:
                raise ValueError(
                    "Edited wording or a clarification question must contain text without NUL characters"
                )
            if self.action == "clarify" and len(self.response) > 1000:
                raise ValueError("A clarification question must fit 1,000 characters")
        elif self.response is not None:
            raise ValueError("Only edit or clarify decisions supply response text")
        return self


class DecisionSummary(BaseModel):
    id: UUID
    actor_id: UUID
    action: str
    reason: str
    response: str | None
    created_at: datetime
    revision: int
