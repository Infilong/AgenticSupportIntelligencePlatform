from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import PromptTemplate


class PromptTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_default(
        self,
        *,
        workspace_id: UUID,
        name: str,
        language: SupportedLanguage,
        template_text: str,
        version: int = 1,
    ) -> PromptTemplate:
        template = self.db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.name == name,
                PromptTemplate.language == language,
                PromptTemplate.version == version,
            )
        )
        if template is not None:
            return template
        template = PromptTemplate(
            workspace_id=workspace_id,
            name=name,
            language=language,
            version=version,
            template_text=template_text,
            active=True,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
