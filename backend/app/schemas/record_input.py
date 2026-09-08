"""Bounded original input and caller-declared source; identity comes from authentication."""

import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.core.language import SupportedLanguage


class RecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["text", "json"] = "text"
    content: str | dict[str, JsonValue] | list[JsonValue]
    source: Literal["api", "admin", "cli", "unknown"] = "api"
    source_reference: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def validate_content(self):
        if self.format == "text" and not isinstance(self.content, str):
            raise ValueError("Text input requires a string.")
        if self.format == "json" and not isinstance(self.content, (dict, list)):
            raise ValueError("JSON input requires an object or array.")
        text = self.processing_text()
        if not text.strip() or len(text) > 12000:
            raise ValueError("Input must contain 1–12000 characters.")
        if self.content in ({}, []):
            raise ValueError("JSON input must not be empty.")
        return self

    def processing_text(self) -> str:
        return self.content if isinstance(self.content, str) else json.dumps(
            self.content, ensure_ascii=False, sort_keys=True, allow_nan=False)

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(), ensure_ascii=False, sort_keys=True, allow_nan=False)


class RecordCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_id: UUID
    request_key: str = Field(min_length=1, max_length=100)
    input: RecordInput
    language: SupportedLanguage | None = None


class RecordClarificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: UUID
    request_key: str = Field(min_length=1, max_length=100)
    reply: str = Field(min_length=1, max_length=2000)
