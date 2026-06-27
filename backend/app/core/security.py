from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError

from app.core.config import Settings

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390_000
SALT_BYTES = 16


class TokenError(ValueError):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return "$".join(
        [
            PASSWORD_SCHEME,
            str(PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected_digest = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(subject: str, settings: Settings) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise TokenError("Invalid access token.") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenError("Invalid access token subject.")
    return subject
