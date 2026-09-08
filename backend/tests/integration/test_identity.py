from datetime import timedelta

from sqlalchemy.orm import Session

from app.modules.identity.models import LoginSession
from app.modules.identity.security import COOKIE, digest, now
from tests.integration.conftest import ORIGIN, PASSWORD, login


def test_login_rotation_logout_and_replay(system):
    client = system["client"]
    prelogin = client.get("/api/session")
    assert prelogin.json()["user"] is None
    old = client.cookies[COOKIE]
    headers = login(client)
    authenticated = client.cookies[COOKIE]
    assert old != authenticated
    assert client.get("/api/workspaces").status_code == 200
    assert client.post("/api/session/logout", headers=headers).status_code == 204
    client.cookies.set(COOKIE, authenticated)
    assert client.get("/api/workspaces").status_code == 401
    client.cookies.set(COOKIE, old)
    assert client.get("/api/workspaces").status_code == 401
    cookie = prelogin.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "path=/" in cookie


def test_login_csrf_and_generic_failure(system):
    client = system["client"]
    csrf = client.get("/api/session").json()["csrf_token"]
    body = {"email": "admin@example.test", "password": PASSWORD}
    for headers in (
        {},
        {"Origin": ORIGIN},
        {"Origin": "https://evil.test", "X-CSRF-Token": csrf},
        {"Origin": ORIGIN, "X-CSRF-Token": "wrong"},
    ):
        assert client.post("/api/session/login", json=body, headers=headers).status_code == 403
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    wrong = client.post("/api/session/login", json={**body, "password": "wrong"}, headers=headers)
    missing = client.post(
        "/api/session/login", json={**body, "email": "unknown@example.test"}, headers=headers
    )
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json()


def test_absolute_and_idle_expiry(system):
    client = system["client"]
    for attribute in ("expires_at", "last_seen_at"):
        login(client)
        with Session(system["engine"]) as db:
            session = db.get(LoginSession, digest(client.cookies[COOKIE]))
            setattr(session, attribute, now() - timedelta(days=1))
            db.commit()
        assert client.get("/api/workspaces").status_code == 401


def test_login_throttles_and_validation_does_not_echo_password(system):
    client = system["client"]
    csrf = client.get("/api/session").json()["csrf_token"]
    headers = {"Origin": ORIGIN, "X-CSRF-Token": csrf}
    for _ in range(10):
        assert (
            client.post(
                "/api/session/login", json={"email": "none@example.test", "password": "bad"}, headers=headers
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/session/login", json={"email": "none@example.test", "password": "bad"}, headers=headers
        ).status_code
        == 429
    )
    response = client.post(
        "/api/session/login",
        json={"email": "admin@example.test", "password": "private" * 60},
        headers=headers,
    )
    assert response.status_code == 422 and "private" not in response.text
