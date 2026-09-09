"""CLI session reuse validates identity/CSRF and does not repeatedly submit passwords."""

import importlib.util
import json
from pathlib import Path

import httpx
import pytest

SOURCE = Path(__file__).resolve().parents[3] / "evals/generation_session.py"
SPEC = importlib.util.spec_from_file_location("generation_session", SOURCE)
session_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(session_module)
CREDENTIALS = {"accounts": {"admin": "admin@example.test"}, "password": "synthetic"}


def test_saved_session_reuses_cookie_and_current_csrf(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "ROOT", tmp_path)
    path = tmp_path / ".artifacts/session.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"asi_rebuild_session": "synthetic-token"}))
    requests = []

    def handle(request):
        requests.append(request)
        assert request.method == "GET"
        assert "asi_rebuild_session=synthetic-token" in request.headers["cookie"]
        return httpx.Response(
            200, json={"csrf_token": "current-csrf", "user": {"email": "admin@example.test"}}
        )

    with httpx.Client(base_url="http://127.0.0.1:8010", transport=httpx.MockTransport(handle)) as client:
        session_module.authenticate(client, CREDENTIALS, path)
        assert client.headers["X-CSRF-Token"] == "current-csrf"
    assert len(requests) == 1


def test_expired_session_refreshes_and_saves_replacement(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "ROOT", tmp_path)
    path = tmp_path / ".artifacts/session.json"

    def handle(request):
        if request.method == "GET":
            return httpx.Response(200, json={"csrf_token": "anonymous", "user": None})
        assert request.headers["X-CSRF-Token"] == "anonymous"
        return httpx.Response(
            200,
            json={"csrf_token": "authenticated"},
            headers={"set-cookie": "asi_rebuild_session=replacement; Path=/"},
        )

    with httpx.Client(base_url="http://127.0.0.1:8010", transport=httpx.MockTransport(handle)) as client:
        session_module.authenticate(client, CREDENTIALS, path)
        assert client.headers["X-CSRF-Token"] == "authenticated"
    assert json.loads(path.read_text()) == {"asi_rebuild_session": "replacement"}


def test_rejects_session_outside_ignored_artifacts_before_network(tmp_path, monkeypatch):
    monkeypatch.setattr(session_module, "ROOT", tmp_path)
    with httpx.Client(base_url="http://127.0.0.1:8010") as client:
        with pytest.raises(ValueError, match="ignored"):
            session_module.authenticate(client, CREDENTIALS, tmp_path / "tracked-session.json")
