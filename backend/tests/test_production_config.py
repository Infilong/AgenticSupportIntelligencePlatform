import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("environment", ["staging", "production", " PRODUCTION "])
@pytest.mark.parametrize("secret", [None, "", "short-private-secret", " " * 40,
                                   " change-this-local-development-secret "])
def test_production_rejects_unsafe_signing_keys(monkeypatch, environment, secret):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    values = {"environment": environment, "_env_file": None}
    if secret is not None:
        values["jwt_secret_key"] = secret
    with pytest.raises(ValidationError) as error:
        Settings(**values)
    assert "requires a non-default JWT_SECRET_KEY" in str(error.value)
    assert "short-private-secret" not in str(error.value)
    assert "change-this-local-development-secret" not in str(error.value)


@pytest.mark.parametrize("environment", ["local", "development", "test"])
def test_local_settings_keep_development_defaults(monkeypatch, environment):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    assert Settings(environment=environment, _env_file=None).jwt_secret_key


def test_production_accepts_explicit_signing_key():
    # Synthetic test value; deployments must generate a random secret.
    secret = "synthetic-production-signing-key-for-test-only"
    settings = Settings(environment="production", jwt_secret_key=secret, _env_file=None)
    assert settings.jwt_secret_key == secret


def test_environment_typo_cannot_silently_disable_guard():
    with pytest.raises(ValidationError):
        Settings(environment="prodution", _env_file=None)


def test_environment_variables_enforce_guard(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short-private-secret")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
    monkeypatch.setenv("JWT_SECRET_KEY", "synthetic-production-signing-key-for-test-only")
    assert Settings(_env_file=None).environment == "production"


def test_signing_key_byte_length_boundary():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret_key="x" * 31, _env_file=None)
    settings = Settings(environment="production", jwt_secret_key="x" * 32, _env_file=None)
    assert settings.jwt_secret_key == "x" * 32
