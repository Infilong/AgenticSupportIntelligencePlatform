from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, normalize_email, verify_password
from app.models.user import User


class DuplicateEmailError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, *, email: str, password: str, display_name: str) -> User:
        user = User(
            email=normalize_email(email),
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEmailError("Email is already registered.") from exc
        self.db.refresh(user)
        return user

    def login(self, *, email: str, password: str) -> str:
        user = self.get_user_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")
        return create_access_token(str(user.id), get_settings())

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == normalize_email(email))
        return self.db.scalar(statement)

    def get_user_by_id(self, user_id: str | UUID) -> User | None:
        try:
            parsed_user_id = user_id if isinstance(user_id, UUID) else UUID(user_id)
        except ValueError:
            return None
        return self.db.get(User, parsed_user_id)
