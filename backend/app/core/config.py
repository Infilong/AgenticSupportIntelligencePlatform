from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multilingual Agentic Support Intelligence Platform"
    environment: str = "local"
    database_url: str = "postgresql+psycopg://agentic:agentic@localhost:5432/agentic_support"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
