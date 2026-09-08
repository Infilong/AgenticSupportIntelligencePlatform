from fastapi import Request
from sqlalchemy.orm import Session


def database(request: Request):
    with Session(request.app.state.engine, expire_on_commit=False) as session:
        yield session
