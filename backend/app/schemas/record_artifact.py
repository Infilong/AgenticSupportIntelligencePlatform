"""Saved intermediate outputs with explicit provenance and decoding failures."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class RecordArtifact(BaseModel):
    step_id: UUID
    run_id: UUID
    kind: str
    created_at: datetime
    status: str
    data: dict[str, Any]
    error: str | None


class RecordArtifactPage(BaseModel):
    items: list[RecordArtifact]
    total: int
    offset: int
    limit: int
    has_next: bool
