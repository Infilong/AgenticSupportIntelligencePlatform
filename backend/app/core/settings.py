from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASI_", hide_input_in_errors=True)

    database_url: SecretStr
    provider_mode: str = "mock"

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
