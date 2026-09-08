from functools import lru_cache
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multilingual Agentic Support Intelligence Platform"
    frontend_dist_path: str | None = None
    environment: Literal["local", "development", "test", "staging", "production"] = "local"
    database_url: str = "postgresql+psycopg://agentic:agentic@localhost:5432/agentic_support"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-this-local-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: int = 30
    embedding_provider: Literal["mock", "openai"] = "mock"
    embedding_model: Literal["text-embedding-3-small", "text-embedding-3-large"] = (
        "text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536, ge=1, le=3072)
    embedding_token_cost_per_1k: float | None = Field(default=None, gt=0, allow_inf_nan=False)

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", hide_input_in_errors=True,
        validate_default=True,
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("embedding_token_cost_per_1k", mode="before")
    @classmethod
    def empty_embedding_price(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def validate_embedding_configuration(self):
        if self.embedding_provider == "openai":
            if not self.openai_api_key or not self.openai_api_key.strip():
                raise ValueError("OpenAI embeddings require OPENAI_API_KEY")
            if self.embedding_token_cost_per_1k is None:
                raise ValueError("OpenAI embeddings require EMBEDDING_TOKEN_COST_PER_1K")
            limit = 1536 if self.embedding_model == "text-embedding-3-small" else 3072
            if self.embedding_dimensions > limit:
                raise ValueError("Embedding dimensions exceed the selected model limit")
            if not 1 <= self.openai_timeout_seconds <= 120:
                raise ValueError("Embedding timeout must be between 1 and 120 seconds")
        return self

    @field_validator("jwt_secret_key")
    @classmethod
    def require_production_signing_key(cls, value: str, info: ValidationInfo) -> str:
        if info.data.get("environment") in {"staging", "production"}:
            candidate = value.strip()
            if candidate == "change-this-local-development-secret" or len(candidate.encode()) < 32:
                raise ValueError(
                    "Staging/production requires a non-default JWT_SECRET_KEY of at least 32 bytes"
                )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
