import json
import logging
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.parametrize("origin", [None, "http://localhost:5173", "https://untrusted.example"])
def test_unexpected_error_has_safe_correlated_reference(caplog, origin):
    app = create_app()

    @app.get("/synthetic-failure")
    def fail():
        raise RuntimeError("private customer and provider credential")

    logger = logging.getLogger("asi.http")
    logger.addHandler(caplog.handler)
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/synthetic-failure?private=secret", headers={
                **({"Origin": origin} if origin else {}), "X-Request-ID": "untrusted-client-id",
            })
    finally:
        logger.removeHandler(caplog.handler)
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    reference = response.headers["x-request-id"]
    assert str(UUID(reference)) == reference
    assert response.json() == {"detail": {
        "code": "internal_error", "message": "An internal error occurred.",
        "request_id": reference,
    }}
    outcome, = [json.loads(row.message) for row in caplog.records if row.name == "asi.http"]
    assert outcome["request_id"] == reference
    assert outcome["error_type"] == "RuntimeError"
    assert "private" not in response.text
    assert "untrusted-client-id" not in response.text
    expected_origin = origin if origin == "http://localhost:5173" else None
    assert response.headers.get("access-control-allow-origin") == expected_origin
    if expected_origin:
        assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


@pytest.mark.parametrize("denied", [False, True])
def test_normal_cors_responses_expose_request_id(denied):
    app = create_app()

    @app.get("/synthetic-response")
    def respond():
        if denied:
            raise HTTPException(status_code=403, detail="Denied")
        return {"ok": True}

    with TestClient(app) as client:
        response = client.get("/synthetic-response", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == (403 if denied else 200)
    assert "x-request-id" in response.headers["access-control-expose-headers"].lower()


def test_unexpected_error_is_not_swallowed_by_safe_response_handler():
    app = create_app()
    failure = RuntimeError("synthetic internal failure")

    @app.get("/synthetic-unhandled")
    def fail():
        raise failure

    with TestClient(app) as client:
        with pytest.raises(RuntimeError) as raised:
            client.get("/synthetic-unhandled")
    assert raised.value is failure
