from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.language import SupportedLanguage
from app.schemas.agent import GraphRunResponse

TaskRunStatusFilter = Literal["all", "queued", "running", "stopping", "stopped",
                              "completed", "needs_human_review", "failed", "rejected",
                              "awaiting_clarification"]


class TaskCreateRequest(BaseModel):
    agent_id: UUID
    input_message: str = Field(min_length=1, max_length=4000)
    request_key: str = Field(min_length=1, max_length=100)
    language: SupportedLanguage | None = None


class TaskRunResponse(BaseModel):
    task_id: UUID | None
    run: GraphRunResponse
    parent_run_id: UUID | None = None
    corrected_instructions: str | None = None
    clarification_reply: str | None = None


class TaskRetryRequest(BaseModel):
    request_key: str = Field(min_length=1, max_length=100)
    corrected_instructions: str = Field(min_length=1, max_length=2000)


class TaskAttemptPage(BaseModel):
    items: list[TaskRunResponse]
    total: int
    has_next: bool
