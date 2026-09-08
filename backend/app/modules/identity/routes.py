from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select

from app.modules.identity.dependencies import Database
from app.modules.identity.models import LoginSession, User
from app.modules.identity.security import (
    COOKIE,
    DUMMY_HASH,
    check_csrf,
    issue_session,
    now,
    passwords,
    prune_expired,
    read_session,
    throttle,
)

router = APIRouter(prefix="/api/session", tags=["session"])


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


def identity_payload(db, session):
    user = db.get(User, session.user_id) if session.user_id else None
    return {
        "user": {"id": str(user.id), "email": user.email, "display_name": user.display_name}
        if user
        else None,
        "csrf_token": session.csrf_token,
    }


@router.get("")
def get_session(request: Request, response: Response, db: Database):
    response.headers["Cache-Control"] = "no-store"
    session = read_session(db, request)
    if session is None:
        prune_expired(db)
        throttle(db, "preauth:" + (request.client.host if request.client else "unknown"), limit=120)
        session = issue_session(db, response, request.app.state.settings)
    return identity_payload(db, session)


@router.post("/login")
def login(body: Credentials, request: Request, response: Response, db: Database):
    session = read_session(db, request)
    check_csrf(request, session)
    email = body.email.strip().casefold()
    throttle(db, "login-client:" + (request.client.host if request.client else "unknown"), limit=120)
    throttle(db, email)
    user = db.scalar(select(User).where(User.email == email))
    valid = passwords.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not valid or user is None:
        raise HTTPException(401, "Email or password is incorrect")
    consumed = db.execute(
        delete(LoginSession)
        .where(LoginSession.token_hash == session.token_hash, LoginSession.expires_at > now())
        .returning(LoginSession.token_hash)
    ).scalar_one_or_none()
    if consumed is None:
        raise HTTPException(409, "Session changed; refresh and sign in again")
    # Session replacement and revocation commit together inside issue_session.
    replacement = issue_session(db, response, request.app.state.settings, user.id)
    return identity_payload(db, replacement)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Database):
    session = read_session(db, request)
    check_csrf(request, session)
    db.delete(session)
    db.commit()
    response.delete_cookie(
        COOKIE, path="/", secure=request.app.state.settings.secure_cookies, httponly=True, samesite="lax"
    )
    response.headers["Cache-Control"] = "no-store"
