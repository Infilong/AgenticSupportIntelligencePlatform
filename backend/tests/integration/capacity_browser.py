"""Optional real browser verification against disposable test API/frontend processes."""

import json
import os
import shutil
import signal
import socket
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path
from time import monotonic, sleep

import httpx

from tests.integration.conftest import PASSWORD


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def stop(process):
    if process.poll() is None:
        if os.name == "nt":
            # The live Popen handle confirms this is still our launcher, not a reused PID.
            result = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode and process.poll() is None:
                raise RuntimeError("Could not stop the owned capacity process tree")
        else:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=10)


def launch(command, **options):
    return subprocess.Popen(
        command,
        **options,
        start_new_session=os.name != "nt",
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def ready(process, url):
    deadline = monotonic() + 30
    while monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Capacity test server exited; inspect its saved log")
        try:
            if httpx.get(url, timeout=2).status_code == 200:
                return
        except httpx.TransportError:
            pass  # Bounded startup readiness polling; failures stay in the server log.
        sleep(0.1)
    raise RuntimeError("Capacity test server did not become ready within 30 seconds")


def verify_browser(system, directory):
    root = Path(__file__).resolve().parents[3]
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required for capacity browser verification")
    frontend = root / "frontend"
    api_port, web_port = free_port(), free_port()
    while web_port == api_port:
        web_port = free_port()
    api_url, web_url = f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{web_port}"
    credentials = directory / "capacity-credentials.json"
    credentials.write_text(
        json.dumps({"email": "viewer@example.test", "password": PASSWORD}), encoding="utf-8"
    )
    env = {
        **os.environ,
        "ASI_DATABASE_URL": system["engine"].url.render_as_string(hide_password=False),
        "ASI_ALLOWED_ORIGINS": json.dumps([web_url]),
        "ASI_API_TARGET": api_url,
        "ASI_CAPACITY_WEB_URL": web_url,
        "ASI_CAPACITY_CREDENTIALS": str(credentials),
        "ASI_CAPACITY_WORKSPACE": str(system["workspace"]),
        "ASI_CAPACITY_FOREIGN": str(system["foreign"]),
        "PLAYWRIGHT_BROWSERS_PATH": str(root / ".artifacts" / "browsers"),
        "ASI_EVIDENCE_DIR": str(directory / "browser"),
    }
    with ExitStack() as stack:
        api_log = stack.enter_context((directory / "capacity-api.log").open("wb"))
        api = launch(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
                "--no-access-log",
            ],
            cwd=root / "backend",
            env=env,
            stdout=api_log,
            stderr=subprocess.STDOUT,
        )
        stack.callback(stop, api)
        ready(api, f"{api_url}/api/health/ready")
        web_log = stack.enter_context((directory / "capacity-web.log").open("wb"))
        web = launch(
            [
                node,
                str(frontend / "node_modules/vite/bin/vite.js"),
                "--host",
                "127.0.0.1",
                "--port",
                str(web_port),
                "--strictPort",
            ],
            cwd=frontend,
            env=env,
            stdout=web_log,
            stderr=subprocess.STDOUT,
        )
        stack.callback(stop, web)
        ready(web, web_url)
        # No route interception or mock API: Vite proxies to the real application on the test schema.
        browser_log = stack.enter_context((directory / "capacity-browser.log").open("wb"))
        browser = launch(
            [
                node,
                str(frontend / "node_modules/@playwright/test/cli.js"),
                "test",
                "tests/e2e/inbox-capacity.spec.ts",
            ],
            cwd=frontend,
            env=env,
            stdout=browser_log,
            stderr=subprocess.STDOUT,
        )
        stack.callback(stop, browser)
        # Stream logs before waiting so timeout/launcher failure cannot discard diagnostics.
        code = browser.wait(timeout=120)
        assert code == 0, "Capacity browser failed; inspect capacity-browser.log and traces"
