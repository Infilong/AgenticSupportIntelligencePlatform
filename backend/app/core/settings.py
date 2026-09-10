from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GenerationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASI_", hide_input_in_errors=True)

    generation_mode: Literal["manual", "local_ollama"] = "manual"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"

    @field_validator("ollama_url")
    @classmethod
    def local_endpoint(cls, value):
        parsed = urlparse(value)
        if (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "localhost", "host.docker.internal"}
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Use the local Ollama HTTP endpoint")
        return value.rstrip("/")


class Settings(GenerationSettings):
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
