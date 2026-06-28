from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.language import SupportedLanguage


class PromptTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    language: SupportedLanguage
    version: int
    template_text: str
    active: bool
    archived_at: datetime | None
    created_at: datetime


class PromptTemplateCreateVersionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    language: SupportedLanguage
    template_text: str = Field(min_length=20, max_length=12000)
    active: bool = True

    @field_validator("name", "template_text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value cannot be blank")
        return stripped
