"""Agent-specific settings extending the existing update contract."""

from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.agent import AgentUpdateRequest as BaseAgentUpdateRequest


class AgentUpdateRequest(BaseAgentUpdateRequest):
    instructions: str | None = Field(default=None, max_length=4000)
    knowledge_document_ids: list[UUID] | None = Field(default=None, max_length=100)
    allowed_actions: list[Literal["set_category", "add_note"]] | None = Field(
        default=None, max_length=2)

    @field_validator("instructions")
    @classmethod
    def trim_instructions(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None
