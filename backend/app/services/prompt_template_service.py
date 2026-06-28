from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import PromptTemplate


class PromptTemplateNotFoundError(ValueError):
    pass


class PromptTemplateService:
    def __init__(self, db: Session):
        self.db = db

    def list_templates(
        self, *, workspace_id: UUID, include_archived: bool = False
    ) -> list[PromptTemplate]:
        filters = [PromptTemplate.workspace_id == workspace_id]
        if not include_archived:
            filters.append(PromptTemplate.archived_at.is_(None))
        return list(
            self.db.scalars(
                select(PromptTemplate)
                .where(*filters)
                .order_by(
                    PromptTemplate.name.asc(),
                    PromptTemplate.language.asc(),
                    PromptTemplate.archived_at.is_not(None),
                    PromptTemplate.version.desc(),
                )
            ).all()
        )

    def get_active_or_create_default(
        self,
        *,
        workspace_id: UUID,
        name: str,
        language: SupportedLanguage,
        template_text: str,
    ) -> PromptTemplate:
        active_template = self.db.scalar(
            select(PromptTemplate)
            .where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.name == name,
                PromptTemplate.language == language,
                PromptTemplate.active.is_(True),
                PromptTemplate.archived_at.is_(None),
            )
            .order_by(PromptTemplate.version.desc())
        )
        if active_template is not None:
            return active_template
        return self.create_version(
            workspace_id=workspace_id,
            name=name,
            language=language,
            template_text=template_text,
            active=True,
        )

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
                PromptTemplate.archived_at.is_(None),
            )
        )
        if template is not None:
            return template
        archived_version = self.db.scalar(
            select(PromptTemplate.id).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.name == name,
                PromptTemplate.language == language,
                PromptTemplate.version == version,
            )
        )
        return self.create_version(
            workspace_id=workspace_id,
            name=name,
            language=language,
            template_text=template_text,
            active=True,
            version=None if archived_version is not None else version,
        )

    def create_version(
        self,
        *,
        workspace_id: UUID,
        name: str,
        language: SupportedLanguage,
        template_text: str,
        active: bool,
        version: int | None = None,
    ) -> PromptTemplate:
        resolved_name = name.strip()
        resolved_text = template_text.strip()
        resolved_version = version or self._next_version(
            workspace_id=workspace_id, name=resolved_name, language=language
        )
        if active:
            self._deactivate_family(
                workspace_id=workspace_id, name=resolved_name, language=language
            )
        template = PromptTemplate(
            workspace_id=workspace_id,
            name=resolved_name,
            language=language,
            version=resolved_version,
            template_text=resolved_text,
            active=active,
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def activate(self, *, workspace_id: UUID, template_id: UUID) -> PromptTemplate:
        template = self.db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.id == template_id,
                PromptTemplate.archived_at.is_(None),
            )
        )
        if template is None:
            raise PromptTemplateNotFoundError("Prompt template was not found.")
        self._deactivate_family(
            workspace_id=workspace_id, name=template.name, language=template.language
        )
        template.active = True
        self.db.commit()
        self.db.refresh(template)
        return template

    def archive(self, *, workspace_id: UUID, template_id: UUID) -> PromptTemplate:
        template = self.db.scalar(
            select(PromptTemplate).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.id == template_id,
            )
        )
        if template is None:
            raise PromptTemplateNotFoundError("Prompt template was not found.")
        template.active = False
        if template.archived_at is None:
            template.archived_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(template)
        return template

    def _next_version(
        self, *, workspace_id: UUID, name: str, language: SupportedLanguage
    ) -> int:
        current = self.db.scalar(
            select(func.coalesce(func.max(PromptTemplate.version), 0)).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.name == name,
                PromptTemplate.language == language,
            )
        )
        return int(current or 0) + 1

    def _deactivate_family(
        self, *, workspace_id: UUID, name: str, language: SupportedLanguage
    ) -> None:
        templates = self.db.scalars(
            select(PromptTemplate).where(
                PromptTemplate.workspace_id == workspace_id,
                PromptTemplate.name == name,
                PromptTemplate.language == language,
                PromptTemplate.active.is_(True),
                PromptTemplate.archived_at.is_(None),
            )
        ).all()
        for template in templates:
            template.active = False
        self.db.flush()
