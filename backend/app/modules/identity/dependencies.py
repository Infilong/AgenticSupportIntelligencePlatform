from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import database
from app.modules.identity.models import User
from app.modules.identity.security import check_csrf, now, read_session

Database = Annotated[Session, Depends(database)]


def current_user(request: Request, db: Database):
    session = read_session(db, request)
    if session is None or session.user_id is None:
        raise HTTPException(401, "Sign in to continue")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_csrf(request, session)
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(401, "Sign in to continue")
    session.last_seen_at = now()
    db.commit()
    return user


CurrentUser = Annotated[User, Depends(current_user)]
