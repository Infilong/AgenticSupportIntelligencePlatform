"""Operate the separate, loopback-only local release stack without touching development data."""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / ".artifacts" / "m6"
ENVIRONMENT = DIRECTORY / "release.env"
CREDENTIALS = DIRECTORY / "release-credentials.json"


def compose(*arguments, env=None):
    if not ENVIRONMENT.is_file():
        raise RuntimeError("Run release-up to initialize the separate release environment")
    return subprocess.run(["docker", "compose", "--env-file", str(ENVIRONMENT),
                           "-f", str(ROOT / "infra/compose.release.yaml"), "-p", "asi-release-v1",
                           *arguments], cwd=ROOT, env=env, check=True, timeout=600)


def main(action):
    if action == "up":
        DIRECTORY.mkdir(parents=True, exist_ok=True)
        if not ENVIRONMENT.exists():
            with ENVIRONMENT.open("x", encoding="utf-8") as output:
                output.write(f"ASI_RELEASE_DATABASE_PASSWORD={secrets.token_urlsafe(32)}\n")
        compose("up", "-d", "--wait", "postgres")
        compose("build", "api")
        compose("stop", "--timeout", "30", "api", "worker")
        compose("run", "--rm", "--no-deps", "api", "uv", "run", "--frozen", "alembic", "upgrade", "head")
        compose("run", "--rm", "--no-deps", "api", "uv", "run", "--frozen", "python", "-m", "app.workflows.checkpoints")
        compose("up", "-d", "--wait", "api", "worker")
        print("Local release: http://127.0.0.1:8011; separate database/model volumes; no Vite service.")
    elif action == "seed":
        if not ENVIRONMENT.is_file():
            raise RuntimeError("Run release-up first")
        if not CREDENTIALS.exists():
            with CREDENTIALS.open("x", encoding="utf-8") as output:
                json.dump({"password": secrets.token_urlsafe(24), "accounts": {
                    role: f"{role}@asterworks.example" for role in ("admin", "operator", "viewer", "private")}}, output)
        password = json.loads(CREDENTIALS.read_text(encoding="utf-8"))["password"]
        compose("run", "--rm", "--no-deps", "-e", "ASI_DEMO_PASSWORD", "api", "uv", "run", "--frozen",
                "python", "-m", "app.bootstrap", env={**os.environ, "ASI_DEMO_PASSWORD": password})
        print(f"Separate synthetic release credentials: {CREDENTIALS}")
    elif action == "prepare-model":
        compose("run", "--rm", "--no-deps", "api", "uv", "run", "--frozen", "python", "-m", "app.providers.prepare_model")
    elif action == "down":
        compose("down")  # Preserve both release volumes; never operate on development/archive projects.
    else:
        raise ValueError("Unknown local release action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
