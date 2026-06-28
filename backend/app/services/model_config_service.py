from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig
from app.models.ai import ModelConfig
from app.services.token_accounting import ModelPricing, pricing_for_model


class ModelConfigNotFoundError(ValueError):
    pass


class ModelConfigService:
    def __init__(self, db: Session):
        self.db = db

    def list_configs(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool = False,
        status_filter: str = "all",
        search: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelConfig]:
        filters = _model_config_filters(
            workspace_id=workspace_id,
            include_archived=include_archived,
            status_filter=status_filter,
            search=search,
        )
        statement = (
            select(ModelConfig)
            .where(*filters)
            .order_by(
                ModelConfig.purpose.asc(),
                ModelConfig.active.desc(),
                ModelConfig.archived_at.is_not(None),
                ModelConfig.created_at.desc(),
            )
            .offset(offset)
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.db.scalars(statement).all())

    def count_configs(
        self,
        *,
        workspace_id: UUID,
        include_archived: bool = False,
        status_filter: str = "all",
        search: str | None = None,
    ) -> int:
        filters = _model_config_filters(
            workspace_id=workspace_id,
            include_archived=include_archived,
            status_filter=status_filter,
            search=search,
        )
        total = self.db.scalar(select(func.count(ModelConfig.id)).where(*filters))
        return int(total or 0)

    def create_config(
        self,
        *,
        workspace_id: UUID,
        provider: str,
        model: str,
        purpose: str,
        prompt_token_cost_per_1k: float,
        completion_token_cost_per_1k: float,
        max_context_tokens: int,
        active: bool,
    ) -> ModelConfig:
        resolved_provider = provider.strip()
        resolved_model = model.strip()
        resolved_purpose = purpose.strip()
        if active:
            self._deactivate_purpose(workspace_id=workspace_id, purpose=resolved_purpose)
        config = ModelConfig(
            workspace_id=workspace_id,
            provider=resolved_provider,
            model=resolved_model,
            purpose=resolved_purpose,
            prompt_token_cost_per_1k=prompt_token_cost_per_1k,
            completion_token_cost_per_1k=completion_token_cost_per_1k,
            max_context_tokens=max_context_tokens,
            active=active,
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def activate(self, *, workspace_id: UUID, model_config_id: UUID) -> ModelConfig:
        config = self.db.scalar(
            select(ModelConfig).where(
                ModelConfig.workspace_id == workspace_id,
                ModelConfig.id == model_config_id,
                ModelConfig.archived_at.is_(None),
            )
        )
        if config is None:
            raise ModelConfigNotFoundError("Model config was not found.")
        self._deactivate_purpose(workspace_id=workspace_id, purpose=config.purpose)
        config.active = True
        self.db.commit()
        self.db.refresh(config)
        return config

    def archive(self, *, workspace_id: UUID, model_config_id: UUID) -> ModelConfig:
        config = self.get_config(
            workspace_id=workspace_id,
            model_config_id=model_config_id,
            include_archived=True,
        )
        if config is None:
            raise ModelConfigNotFoundError("Model config was not found.")
        config.active = False
        if config.archived_at is None:
            config.archived_at = datetime.now(UTC)
        agents = self.db.scalars(
            select(AgentConfig).where(
                AgentConfig.workspace_id == workspace_id,
                AgentConfig.model_config_id == config.id,
            )
        ).all()
        for agent in agents:
            agent.model_config_id = None
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_config(
        self, *, workspace_id: UUID, model_config_id: UUID, include_archived: bool = False
    ) -> ModelConfig | None:
        filters = [ModelConfig.workspace_id == workspace_id, ModelConfig.id == model_config_id]
        if not include_archived:
            filters.append(ModelConfig.archived_at.is_(None))
        return self.db.scalar(select(ModelConfig).where(*filters))

    def resolve_pricing(
        self,
        *,
        workspace_id: UUID,
        purpose: str,
        fallback_model: str,
        model_config_id: UUID | None = None,
    ) -> ModelPricing:
        config = None
        if model_config_id is not None:
            config = self.get_config(workspace_id=workspace_id, model_config_id=model_config_id)
        if config is None:
            config = self.db.scalar(
                select(ModelConfig)
                .where(
                    ModelConfig.workspace_id == workspace_id,
                    ModelConfig.purpose == purpose,
                    ModelConfig.active.is_(True),
                    ModelConfig.archived_at.is_(None),
                )
                .order_by(ModelConfig.created_at.desc())
            )
        if config is None:
            return pricing_for_model(fallback_model)
        return ModelPricing(
            provider=config.provider,
            model=config.model,
            model_config_id=config.id,
            prompt_token_cost_per_1k=config.prompt_token_cost_per_1k,
            completion_token_cost_per_1k=config.completion_token_cost_per_1k,
            max_context_tokens=config.max_context_tokens,
        )

    def _deactivate_purpose(self, *, workspace_id: UUID, purpose: str) -> None:
        configs = self.db.scalars(
            select(ModelConfig).where(
                ModelConfig.workspace_id == workspace_id,
                ModelConfig.purpose == purpose,
                ModelConfig.active.is_(True),
                ModelConfig.archived_at.is_(None),
            )
        ).all()
        for config in configs:
            config.active = False
        self.db.flush()


def _model_config_filters(
    *, workspace_id: UUID, include_archived: bool, status_filter: str, search: str | None
) -> list:
    filters = [ModelConfig.workspace_id == workspace_id]
    if status_filter == "active":
        filters.extend([ModelConfig.active.is_(True), ModelConfig.archived_at.is_(None)])
    elif status_filter == "draft":
        filters.extend([ModelConfig.active.is_(False), ModelConfig.archived_at.is_(None)])
    elif status_filter == "archived":
        filters.append(ModelConfig.archived_at.is_not(None))
    elif not include_archived:
        filters.append(ModelConfig.archived_at.is_(None))

    normalized_search = (search or "").strip()
    if normalized_search:
        pattern = f"%{normalized_search}%"
        filters.append(
            or_(
                ModelConfig.provider.ilike(pattern),
                ModelConfig.model.ilike(pattern),
                ModelConfig.purpose.ilike(pattern),
                cast(ModelConfig.max_context_tokens, String).ilike(pattern),
                cast(ModelConfig.id, String).ilike(pattern),
            )
        )
    return filters
