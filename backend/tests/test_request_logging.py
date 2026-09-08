import json
import logging
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.request_logging import RequestLogMiddleware


@pytest.fixture
def logged_client(caplog):
    app = FastAPI()
    logger = logging.getLogger("test.asi.http")
    caplog.set_level(logging.INFO, logger=logger.name)
    app.add_middleware(RequestLogMiddleware, logger=logger)

    @app.get("/items/{item_id}")
    def item(item_id: str):
        return {"id": item_id}

    @app.get("/denied")
    def denied():
        raise HTTPException(status_code=403, detail="Permission denied")

    @app.get("/failed")
    def failed():
        raise ValueError("sensitive provider content")

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


def records(caplog):
    return [json.loads(record.message) for record in caplog.records
            if record.name == "test.asi.http"]


def test_request_id_matches_log_and_sensitive_input_is_omitted(logged_client, caplog):
    response = logged_client.get(
        "/items/private-customer?token=private-token",
        headers={"Authorization": "Bearer private-key", "X-Request-ID": "untrusted-client-id"},
    )
    record, = records(caplog)
    assert response.status_code == 200
    assert str(UUID(response.headers["x-request-id"])) == record["request_id"]
    assert record["route"] == "/items/{item_id}"
    assert record["duration_ms"] >= 0
    assert record["error_type"] is None
    assert "private" not in json.dumps(record)
    assert "untrusted-client-id" not in json.dumps(record)


@pytest.mark.parametrize("path,status", [("/denied", 403), ("/unknown-sensitive-path", 404)])
def test_denial_and_unmatched_routes_are_logged(logged_client, caplog, path, status):
    response = logged_client.get(path)
    record, = records(caplog)
    assert response.status_code == record["status"] == status
    assert record["route"] == ("/denied" if status == 403 else "<unmatched>")


def test_unhandled_error_is_logged_without_its_message(logged_client, caplog):
    response = logged_client.get("/failed")
    record, = records(caplog)
    assert response.status_code == record["status"] == 500
    assert record["error_type"] == "ValueError"
    assert "sensitive provider content" not in json.dumps(record)


def test_request_ids_are_distinct(logged_client, caplog):
    first = logged_client.get("/items/a")
    second = logged_client.get("/items/b")
    assert first.headers["x-request-id"] != second.headers["x-request-id"]
    assert len(records(caplog)) == 2
