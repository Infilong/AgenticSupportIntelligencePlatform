import json
import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.settings import Settings
from app.main import create_app


def test_invalid_database_configuration_is_redacted():
    with pytest.raises(ValidationError) as error:
        Settings(database_url="sqlite://secret-value")
    assert "secret-value" not in str(error.value)


def test_liveness_and_readiness_separate_and_logs_redact_input(caplog):
    settings = Settings(database_url="postgresql+psycopg://none:none@127.0.0.1:1/unavailable")
    with (
        caplog.at_level(logging.INFO, logger="workbench.requests"),
        TestClient(create_app(settings)) as client,
    ):
        live = client.get("/api/health/live?secret=private", headers={"Authorization": "secret"})
        assert live.status_code == 200
        assert client.get("/api/health/ready").status_code == 503
        assert client.get("/unknown-private-value").status_code == 404
    records = [json.loads(record.message) for record in caplog.records if record.name == "workbench.requests"]
    assert records[0]["request_id"] == live.headers["x-request-id"]
    assert records[1]["status"] == 503
    assert records[2]["route"] == "unmatched"
    assert "private" not in json.dumps(records)
    assert "secret" not in json.dumps(records)
