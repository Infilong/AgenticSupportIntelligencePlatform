from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService, DuplicateEmailError, InvalidCredentialsError

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> UserResponse:
    service = AuthService(db)
    try:
        user = service.register_user(
            email=payload.email,
            password=payload.password,
            display_name=payload.display_name,
        )
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "email_already_registered", "message": "Email is already registered."},
        ) from exc
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    try:
        access_token = service.login(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Invalid email or password."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenResponse(access_token=access_token)
