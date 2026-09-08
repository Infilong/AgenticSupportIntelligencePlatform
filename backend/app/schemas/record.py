"""Public input record summaries, independent of execution trace payloads."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.record_input import RecordInput


class RecordSummary(BaseModel):
    id: UUID
    input_message: str
    received_at: datetime
    created_by_user_id: UUID
    latest_run_id: UUID
    status: str
    result_summary: str | None
    attempt_count: int


class RecordPage(BaseModel):
    items: list[RecordSummary]
    total: int
    offset: int
    limit: int
    has_next: bool


class RecordDetail(RecordSummary):
    input: RecordInput
