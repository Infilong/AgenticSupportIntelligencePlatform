import io
import json
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.cli.commands import execute, watch
from app.cli.errors import CliError
from app.cli.http import api_address
from app.cli.main import main
from app.cli.parser import normalize_options, parser
from app.cli.session import load_token, save_session


def test_session_roundtrip_is_bound_to_api_and_protected(tmp_path):
    path = tmp_path / "session.json"
    save_session(path, "http://127.0.0.1:8000", "synthetic-secret-token")
    assert load_token(path, "http://127.0.0.1:8000") == "synthetic-secret-token"
    if os.name == "nt":
        assert "synthetic-secret-token" not in path.read_text()
    else:
        assert path.stat().st_mode & 0o077 == 0
    with pytest.raises(CliError, match="another API"):
        load_token(path, "http://127.0.0.1:9000")


@pytest.mark.parametrize(
    "url",
    [
        "http://remote.example",
        "https://user:pass@example.com",
        "https://example.com?token=x",
        "https://example.com/path",
    ],
)
def test_credentials_are_not_sent_to_unsafe_origins(url):
    with pytest.raises(CliError):
        api_address(url)


def test_login_never_prints_token_or_password(tmp_path, monkeypatch, capsys):
    class Login:
        def __init__(self, *args):
            pass

        def call(self, path, **kwargs):
            assert path == "/auth/login"
            assert kwargs["body"]["password"] == "synthetic-password"
            return {"access_token": "synthetic-token"}

    monkeypatch.setattr("app.cli.main.Client", Login)
    monkeypatch.setattr("sys.stdin", io.StringIO("synthetic-password\n"))
    assert (
        main(
            [
                "auth",
                "login",
                "--email",
                "qa@example.test",
                "--password-stdin",
                "--session-file",
                str(tmp_path / "session.json"),
                "--json",
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "synthetic-token" not in captured.out + captured.err
    assert "synthetic-password" not in captured.out + captured.err
    assert json.loads(captured.out)["data"]["authenticated"]


def test_task_connection_error_preserves_request_key(monkeypatch, capsys):
    class Offline:
        def __init__(self, *args):
            pass

        def call(self, *args, **kwargs):
            raise CliError("Connection failed", 7)

    monkeypatch.setenv("ASI_TOKEN", "synthetic-token")
    monkeypatch.setattr("app.cli.main.Client", Offline)
    assert (
        main(
            [
                "task",
                "create",
                "--agent",
                str(uuid4()),
                "--message",
                "Refund?",
                "--workspace",
                str(uuid4()),
                "--request-key",
                "retained",
                "--json",
            ]
        )
        == 7
    )
    assert json.loads(capsys.readouterr().err)["error"]["details"]["request_key"] == "retained"


def test_upload_preserves_multilingual_text_and_rejects_oversize(tmp_path):
    file = tmp_path / "policy.md"
    file.write_text("# 返金\n領収書が必要です。", encoding="utf-8")
    args = parser().parse_args(
        normalize_options(
            ["knowledge", "add", str(file), "--workspace", str(uuid4()), "--language", "ja"]
        )
    )
    calls = []
    client = SimpleNamespace(call=lambda path, **kwargs: calls.append((path, kwargs)))
    execute(args, client, lambda _: None)
    assert calls[0][1]["body"]["content"] == file.read_bytes().decode("utf-8")
    file.write_bytes(b"a" * (2 * 1024 * 1024 + 1))
    with pytest.raises(CliError, match="2 MiB"):
        execute(args, client, lambda _: None)
    assert len(calls) == 1


def test_action_resolution_requires_exact_hash_before_transport():
    args = parser().parse_args(
        normalize_options(
            ["review", "approve", str(uuid4()), "--action", "--workspace", str(uuid4())]
        )
    )
    client = SimpleNamespace(call=lambda *args, **kwargs: pytest.fail("must not dispatch"))
    with pytest.raises(CliError, match="expected-hash"):
        execute(args, client, lambda _: None)


def test_watch_stops_at_review_without_resolving_it(monkeypatch):
    statuses = iter(["queued", "running", "needs_human_review"])
    calls, results = [], []

    def call(path, **kwargs):
        calls.append(path)
        return {"run": {"status": next(statuses)}}

    monkeypatch.setattr("app.cli.commands.time.sleep", lambda _: None)
    watch(
        SimpleNamespace(interval=1, timeout=10), SimpleNamespace(call=call), "/run", results.append
    )
    assert [item["run"]["status"] for item in results] == [
        "queued",
        "running",
        "needs_human_review",
    ]
    assert calls == ["/run"] * 3


def test_watch_timeout_does_not_stop_server_work(monkeypatch):
    ticks = iter([0, 0, 0, 2])
    monkeypatch.setattr("app.cli.commands.time.monotonic", lambda: next(ticks))
    monkeypatch.setattr("app.cli.commands.time.sleep", lambda _: None)
    calls = []

    def call(path, **kwargs):
        calls.append(path)
        return {"run": {"status": "running"}}

    with pytest.raises(CliError) as error:
        watch(
            SimpleNamespace(interval=1, timeout=1),
            SimpleNamespace(call=call),
            "/run",
            lambda _: None,
        )
    assert error.value.exit_code == 9
    assert calls == ["/run"]
