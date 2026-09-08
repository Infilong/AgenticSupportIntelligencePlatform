"""Small explicit task-update inputs, shared by proposal creation and approval."""

import hashlib
import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["set_category", "add_note"]
    value: str = Field(min_length=1, max_length=2000)

    @field_validator("value")
    @classmethod
    def nonblank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A nonblank value is required.")
        return value

    def canonical(self) -> str:
        if self.action == "set_category" and len(self.value) > 80:
            raise ValueError("Category must be at most 80 characters.")
        return json.dumps(self.model_dump(), sort_keys=True, ensure_ascii=False)


def proposal_hash(*, workspace_id: UUID, run_id: UUID, task_id: UUID, inputs: str) -> str:
    return hashlib.sha256(json.dumps([str(workspace_id), str(run_id), str(task_id), inputs],
                                    ensure_ascii=False).encode()).hexdigest()


class ActionResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_hash: str = Field(min_length=64, max_length=64)
    decision: Literal["approve", "reject"]
    reason: str = Field(default="", max_length=2000)


class ActionResponse(BaseModel):
    id: UUID
    graph_run_id: UUID
    task_id: UUID
    proposal_hash: str
    inputs: TaskActionInput
    status: str
    reason: str | None
    result: dict | None
    reviewer_id: UUID | None
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def from_proposal(cls, proposal):
        return cls(**{field: getattr(proposal, field) for field in cls.model_fields
                      if field not in {"inputs", "result"}},
                   inputs=TaskActionInput.model_validate_json(proposal.inputs_json),
                   result=json.loads(proposal.result_json) if proposal.result_json else None)
