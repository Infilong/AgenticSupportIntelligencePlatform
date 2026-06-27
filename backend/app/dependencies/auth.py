from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import TokenError, decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(credentials: BearerCredentials, db: DbSession) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "not_authenticated", "message": "Authentication is required."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(credentials.credentials, get_settings())
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid or expired access token."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = AuthService(db).get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid or expired access token."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
