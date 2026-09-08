import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, Response
from pwdlib import PasswordHash
from sqlalchemy import case, delete, select
from sqlalchemy.dialects.postgresql import insert

from app.modules.identity.models import LoginAttempt, LoginSession

COOKIE = "asi_rebuild_session"
passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash("not-a-real-user-password")


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def now():
    return datetime.now(UTC)


def issue_session(db, response: Response, settings, user_id=None):
    token = secrets.token_urlsafe(32)
    seconds = settings.session_seconds if user_id else 900
    session = LoginSession(
        token_hash=digest(token),
        user_id=user_id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=now() + timedelta(seconds=seconds),
        last_seen_at=now(),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return session


def read_session(db, request: Request):
    token = request.cookies.get(COOKIE, "")
    if not token or len(token) > 100:
        return None
    session = db.get(LoginSession, digest(token))
    if session is None:
        return None
    if session.expires_at <= now() or session.last_seen_at < now() - timedelta(
        seconds=request.app.state.settings.session_idle_seconds
    ):
        db.delete(session)
        db.commit()
        return None
    return session


def check_csrf(request, session):
    supplied = request.headers.get("x-csrf-token", "")
    if request.headers.get("origin") not in request.app.state.settings.allowed_origins:
        raise HTTPException(403, "Untrusted request origin")
    if (
        not session
        or not supplied
        or not secrets.compare_digest(supplied.encode(), session.csrf_token.encode())
    ):
        raise HTTPException(403, "Session verification failed; refresh and try again")


def prune_expired(db):
    # Bounded work on anonymous-session creation; expired records need not return their cookies.
    expired = select(LoginSession.token_hash).where(LoginSession.expires_at <= now()).limit(100)
    cutoff = now() - timedelta(minutes=15)
    attempts = select(LoginAttempt.identity_hash).where(LoginAttempt.started_at < cutoff).limit(100)
    db.execute(
        delete(LoginSession).where(LoginSession.token_hash.in_(expired)),
        execution_options={"synchronize_session": False},
    )
    db.execute(
        delete(LoginAttempt).where(
            LoginAttempt.identity_hash.in_(attempts), LoginAttempt.started_at < cutoff
        ),
        execution_options={"synchronize_session": False},
    )
    db.commit()


def throttle(db, identity, limit=10):
    key = digest(identity)
    stamp = now()
    expired = LoginAttempt.started_at < stamp - timedelta(minutes=15)
    statement = insert(LoginAttempt).values(identity_hash=key, started_at=stamp, attempts=1)
    count = db.scalar(
        statement.on_conflict_do_update(
            index_elements=[LoginAttempt.identity_hash],
            set_={
                "started_at": case((expired, stamp), else_=LoginAttempt.started_at),
                "attempts": case((expired, 1), else_=LoginAttempt.attempts + 1),
            },
        ).returning(LoginAttempt.attempts)
    )
    db.commit()
    if count > limit:
        raise HTTPException(429, "Too many login attempts; try later", headers={"Retry-After": "900"})
