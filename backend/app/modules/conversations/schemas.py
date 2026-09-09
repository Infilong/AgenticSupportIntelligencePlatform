from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.modules.support.schemas import MessageInput

Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]


class Labels(BaseModel):
    model_config = ConfigDict(extra="forbid")
    labels: list[Label] = Field(default_factory=list, max_length=10)

    @field_validator("labels")
    @classmethod
    def valid_labels(cls, values):
        values = [value.casefold() for value in values]
        if any(len(value) > 32 for value in values):
            raise ValueError("Normalized labels must fit in 32 characters")
        if any(not all(c.isalnum() or c in " -_" for c in value) for value in values):
            raise ValueError("Labels use letters, numbers, spaces, hyphens or underscores")
        return sorted(set(values))


class ImportRow(MessageInput, Labels):
    pass


class ImportResult(BaseModel):
    id: UUID
    filename: str
    message_count: int


class SavedMessage(BaseModel):
    id: UUID
    original: str
    language: str
    labels: list[str]
    created_at: datetime
    import_filename: str | None
    latest_run_id: UUID | None
