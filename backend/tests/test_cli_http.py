import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from app.cli.errors import CliError
from app.cli.http import Client


@pytest.fixture
def endpoint():
    received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            received.append((self.path, self.headers.get("Authorization")))
            if self.path.endswith("/redirect"):
                self.send_response(302)
                self.send_header("Location", "/credential-leak")
                self.end_headers()
                return
            if self.path.endswith("/denied"):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"detail":{"message":"Permission denied"}}')
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"not JSON")

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append((self.path, self.headers.get("Authorization")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield Client(f"http://127.0.0.1:{server.server_port}", "synthetic-token"), received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_redirect_does_not_forward_credentials(endpoint):
    client, received = endpoint
    with pytest.raises(CliError):
        client.call("/redirect")
    assert received == [("/api/v1/redirect", "Bearer synthetic-token")]


def test_http_permission_denial_has_stable_exit_code(endpoint):
    client, _ = endpoint
    with pytest.raises(CliError) as error:
        client.call("/denied")
    assert error.value.exit_code == 4
    assert str(error.value) == "Permission denied"


def test_real_transport_preserves_utf8_and_rejects_invalid_json(endpoint):
    client, _ = endpoint
    assert client.call("/echo", method="POST", body={"message": "返金 / 退款"}) == {
        "message": "返金 / 退款"
    }
    with pytest.raises(CliError) as error:
        client.call("/invalid")
    assert error.value.exit_code == 7
