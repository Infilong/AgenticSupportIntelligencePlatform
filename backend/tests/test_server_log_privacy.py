import copy
import io
import json
import logging
import logging.config
import subprocess
import sys
from pathlib import Path

import pytest
from uvicorn.config import LOGGING_CONFIG


@pytest.mark.parametrize("kind", ["simple", "chained", "group"])
def test_server_exception_retains_locations_without_private_text(kind):
    config_path = Path(__file__).parents[1] / "app" / "logging.json"
    config = (json.loads(config_path.read_text()) if config_path.exists()
              else copy.deepcopy(LOGGING_CONFIG))
    output = io.StringIO()
    config["handlers"]["default"]["stream"] = output
    logging.config.dictConfig(config)
    try:
        try:
            if kind == "group":
                raise ExceptionGroup("private-group-marker", [ValueError("private-child-marker")])
            try:
                raise ValueError("private-provider-marker")
            except ValueError as cause:
                if kind == "chained":
                    raise RuntimeError("private-customer-marker") from cause
                raise
        except Exception:
            logging.getLogger("uvicorn.error").exception("private-format-marker %s", "private-arg")
        rendered = output.getvalue()
        assert "private-" not in rendered
        assert "test_server_log_privacy.py" in rendered
        assert "test_server_exception_retains_locations_without_private_text" in rendered
        assert ("ExceptionGroup" if kind == "group" else "ValueError") in rendered
    finally:
        logging.config.dictConfig(copy.deepcopy(LOGGING_CONFIG))


def test_real_server_error_response_and_logs_are_safe():
    script = '''
import json, socket, threading, time
from urllib.request import urlopen
from urllib.error import HTTPError
import uvicorn
from app.main import create_app
app = create_app()
@app.get("/synthetic-error")
def fail():
    raise RuntimeError("private-runtime-marker")
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
server = uvicorn.Server(uvicorn.Config(app, log_config="app/logging.json", access_log=False))
worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
worker.start()
try:
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started
    try:
        urlopen(f"http://127.0.0.1:{sock.getsockname()[1]}/synthetic-error", timeout=5)
        raise AssertionError("expected failure")
    except HTTPError as error:
        assert error.code == 500
        payload = json.load(error)
        reference = error.headers["X-Request-ID"]
        assert payload["detail"]["request_id"] == reference
        print(json.dumps({"event": "probe_response", "request_id": reference}))
finally:
    server.should_exit = True
    worker.join(10)
    sock.close()
    assert not worker.is_alive()
'''
    result = subprocess.run([sys.executable, "-c", script], capture_output=True,
                            text=True, timeout=30, check=True)
    output = result.stdout + result.stderr
    assert "private-runtime-marker" not in output
    assert '"event": "server_exception"' in output
    assert '"type": "RuntimeError"' in output
    assert '"function": "fail"' in output
    response = json.loads(result.stdout.strip())
    assert f'"request_id": "{response["request_id"]}"' in result.stderr
    assert '"event": "http_request"' in result.stderr
