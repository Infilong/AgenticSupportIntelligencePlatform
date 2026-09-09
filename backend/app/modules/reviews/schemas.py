from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["approve", "edit", "reject"]
    reason: str = Field(min_length=1, max_length=1000)
    expected_revision: int = Field(ge=0)
    draft_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    response: str | None = Field(default=None, max_length=8000)

    @model_validator(mode="after")
    def valid_text(self):
        if not self.reason.strip() or "\x00" in self.reason:
            raise ValueError("Provide a review reason without NUL characters")
        if self.action == "edit":
            if not self.response or not self.response.strip() or "\x00" in self.response:
                raise ValueError("An edited response must contain text without NUL characters")
        elif self.response is not None:
            raise ValueError("Only an edit decision supplies replacement text")
        return self


class DecisionSummary(BaseModel):
    id: UUID
    actor_id: UUID
    action: str
    reason: str
    response: str | None
    created_at: datetime
    revision: int
