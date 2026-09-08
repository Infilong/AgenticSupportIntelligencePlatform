from datetime import timedelta

from sqlalchemy.orm import Session

from app.modules.identity.models import LoginAttempt, LoginSession
from app.modules.identity.security import COOKIE, digest, now
from tests.integration.conftest import ORIGIN, login


def test_non_ascii_csrf_and_unsafe_origins_are_denied(system):
    client = system["client"]
    headers = login(client)
    url = f"/api/workspaces/{system['workspace']}/members/{system['users']['viewer'].id}"
    invalid_headers = [
        {"Origin": "https://evil.test", "X-CSRF-Token": headers["X-CSRF-Token"]},
        {"Origin": ORIGIN, "X-CSRF-Token": "wrong"},
        [(b"origin", ORIGIN.encode()), (b"x-csrf-token", b"\xff")],
    ]
    for invalid in invalid_headers:
        assert client.patch(url, json={"role": "operator"}, headers=invalid).status_code == 403
        assert client.post("/api/session/logout", headers=invalid).status_code == 403
    assert client.get("/api/workspaces").status_code == 200


def test_anonymous_creation_prunes_expired_rows_but_preserves_valid_sessions(system):
    client = system["client"]
    login(client)
    valid = digest(client.cookies[COOKIE])
    with Session(system["engine"]) as db:
        db.add(
            LoginSession(
                token_hash="expired",
                user_id=None,
                csrf_token="expired",
                expires_at=now() - timedelta(days=1),
                last_seen_at=now() - timedelta(days=1),
            )
        )
        db.add(
            LoginAttempt(identity_hash="expired-attempt", attempts=10, started_at=now() - timedelta(days=1))
        )
        db.commit()
    client.cookies.clear()
    assert client.get("/api/session").status_code == 200
    with Session(system["engine"]) as db:
        assert db.get(LoginSession, "expired") is None
        assert db.get(LoginAttempt, "expired-attempt") is None
        assert db.get(LoginSession, valid) is not None


def test_secure_cookie_configuration(system):
    system["app"].state.settings.secure_cookies = True
    assert "secure" in system["client"].get("/api/session").headers["set-cookie"].lower()


def test_login_throttle_window_resets(system):
    from app.modules.identity.security import throttle

    with Session(system["engine"], expire_on_commit=False) as db:
        db.add(
            LoginAttempt(
                identity_hash=digest("window-test"), attempts=100, started_at=now() - timedelta(minutes=16)
            )
        )
        db.commit()
        throttle(db, "window-test")
        assert db.get(LoginAttempt, digest("window-test")).attempts == 1


def test_counter_refresh_and_cleanup_are_concurrency_safe(system):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.modules.identity.security import prune_expired, throttle

    key = digest("concurrent-counter")
    with Session(system["engine"]) as db:
        db.add(LoginAttempt(identity_hash=key, attempts=100, started_at=now() - timedelta(minutes=16)))
        db.commit()
    barrier = Barrier(2)

    def work(cleanup):
        with Session(system["engine"]) as db:
            barrier.wait(timeout=10)
            for _ in range(20):
                if cleanup:
                    prune_expired(db)
                else:
                    throttle(db, "concurrent-counter", limit=100)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(work, (True, False)))
    with Session(system["engine"]) as db:
        assert db.get(LoginAttempt, key).attempts == 20
