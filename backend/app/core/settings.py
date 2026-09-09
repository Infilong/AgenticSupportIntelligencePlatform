from pathlib import Path

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASI_", hide_input_in_errors=True)

    database_url: SecretStr
    provider_mode: str = "mock"
    embedding_cache: str | None = None
    frontend_dist: Path | None = None
    session_seconds: int = 28800
    session_idle_seconds: int = 3600
    secure_cookies: bool = False  # Local loopback HTTP only; HTTPS deployments must enable this.
    allowed_origins: list[str] = [
        "http://127.0.0.1:5180",
        "http://localhost:5180",
        "http://127.0.0.1:8010",
        "http://localhost:8010",
    ]

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("Use a PostgreSQL psycopg database URL")
        return value

    @field_validator("provider_mode")
    @classmethod
    def supported_provider(cls, value: str) -> str:
        if value != "mock":
            raise ValueError("Only mock development mode is implemented in M1")
        return value
