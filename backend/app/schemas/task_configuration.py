"""Explicit public fields from an immutable admission snapshot."""

import json
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.public_trace import PublicTraceResponse


class TaskConfigurationResponse(PublicTraceResponse):
    name: str
    model_config_id: UUID | None
    token_budget: int
    instructions: str = ""
    knowledge_document_ids: list[UUID] | None = None
    allowed_actions: list[Literal["set_category", "add_note"]] = Field(default_factory=list)

    @classmethod
    def from_snapshot(cls, raw: str):
        snapshot = json.loads(raw)
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("settings", {}), dict):
            raise ValueError("Invalid saved configuration")
        settings = snapshot.get("settings", {})
        return cls(name=snapshot["name"], model_config_id=snapshot.get("model_config_id"),
                   token_budget=snapshot["token_budget"],
                   instructions=settings.get("instructions", ""),
                   knowledge_document_ids=settings.get("knowledge_document_ids"),
                   allowed_actions=settings.get("allowed_actions", []))
