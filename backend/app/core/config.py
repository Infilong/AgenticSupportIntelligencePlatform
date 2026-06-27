from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multilingual Agentic Support Intelligence Platform"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://agentic:agentic@localhost:5432/agentic_support"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-this-local-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
