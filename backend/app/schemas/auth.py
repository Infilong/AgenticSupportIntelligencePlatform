from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.security import normalize_email


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    display_name: str = Field(min_length=1, max_length=120)

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        normalized = normalize_email(value)
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("display_name cannot be blank")
        return stripped


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        return normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
