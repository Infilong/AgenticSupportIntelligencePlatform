from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai import ModelConfig
from app.services.token_accounting import ModelPricing, pricing_for_model


class ModelConfigNotFoundError(ValueError):
    pass


class ModelConfigService:
    def __init__(self, db: Session):
        self.db = db

    def list_configs(self, *, workspace_id: UUID) -> list[ModelConfig]:
        return list(
            self.db.scalars(
                select(ModelConfig)
                .where(ModelConfig.workspace_id == workspace_id)
                .order_by(
                    ModelConfig.purpose.asc(),
                    ModelConfig.active.desc(),
                    ModelConfig.created_at.desc(),
                )
            ).all()
        )

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
            )
        )
        if config is None:
            raise ModelConfigNotFoundError("Model config was not found.")
        self._deactivate_purpose(workspace_id=workspace_id, purpose=config.purpose)
        config.active = True
        self.db.commit()
        self.db.refresh(config)
        return config

    def get_config(self, *, workspace_id: UUID, model_config_id: UUID) -> ModelConfig | None:
        return self.db.scalar(
            select(ModelConfig).where(
                ModelConfig.workspace_id == workspace_id,
                ModelConfig.id == model_config_id,
            )
        )

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
                )
                .order_by(ModelConfig.created_at.desc())
            )
        if config is None:
            return pricing_for_model(fallback_model)
        return ModelPricing(
            provider=config.provider,
            model=config.model,
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
            )
        ).all()
        for config in configs:
            config.active = False
        self.db.flush()
