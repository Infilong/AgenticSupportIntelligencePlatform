"""Verify the built web image against an existing isolated mock Compose stack."""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def inspect_runtime(config: dict, logs: str) -> dict:
    if config != {"uid": 10001, "node": None, "npm": None, "environment": "production"}:
        raise ValueError("Built image must use production mode, UID 10001 and no Node/npm runtime")
    records = []
    for line in logs.splitlines():
        try:
            record = json.loads(line[line.index("{"):])
        except (ValueError, json.JSONDecodeError):
            continue
        if record.get("event") == "http_request":
            records.append(record)
    if not records:
        raise ValueError("Built image produced no HTTP outcome evidence")
    errors = sum(item.get("status", 0) >= 500 or bool(item.get("error_type")) for item in records)
    if errors:
        raise ValueError("Built image runtime contains server/error outcomes")
    return {"http_outcomes": len(records), "server_or_error_outcomes": errors, **config}


def verify(project: str, port: int) -> Path:
    identity = uuid4().hex
    output = ROOT / ".artifacts" / f"built-web-{identity}"
    output.mkdir(parents=True)
    container = f"{project}-web-{identity}"
    image = f"{project}-built-web"
    environment = dict(os.environ)
    environment.update(OPENAI_API_KEY="", EMBEDDING_PROVIDER="mock",
                       JWT_SECRET_KEY=secrets.token_hex(32),
                       API_URL=f"http://127.0.0.1:{port}", FRONTEND_URL=f"http://127.0.0.1:{port}",
                       PLAYWRIGHT_JSON_OUTPUT_NAME=str(output / "browser-results.json"))
    checks = []

    def run(name, command, *, cwd=ROOT, timeout=120, required=True):
        print(f"Running {name}; log: {output / (name + '.log')}", flush=True)
        with (output / f"{name}.log").open("w", encoding="utf-8") as log:
            try:
                result = subprocess.run(command, cwd=cwd, env=environment, stdout=log,
                                        stderr=subprocess.STDOUT, timeout=timeout, check=False)
                code = result.returncode
            except (OSError, subprocess.TimeoutExpired) as error:
                log.write(f"Verification command failed: {type(error).__name__}\n")
                code = 124
        checks.append({"name": name, "command": command, "exit_code": code})
        (output / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        if code and required:
            raise RuntimeError(f"{name} failed; inspect {output / (name + '.log')}")
        return code

    connection = ["--network", f"{project}_default", "-e", "JWT_SECRET_KEY",
                  "-e", "DATABASE_URL=postgresql+psycopg://agentic:agentic@postgres:5432/agentic_support",
                  "-e", "REDIS_URL=redis://redis:6379/0", "-e", "EMBEDDING_PROVIDER=mock",
                  "-e", "OPENAI_API_KEY="]
    migration = container + "-migration"
    worker = container + "-worker"
    try:
        run("build", ["docker", "build", "-f", "infra/Dockerfile.web", "-t", image, "."], timeout=900)
        run("migration", ["docker", "run", "--name", migration, *connection,
                          image, "alembic", "upgrade", "head"], timeout=120)
        run("startup", ["docker", "run", "-d", "--name", container, *connection,
                        "-p", f"127.0.0.1:{port}:8000", image])
        run("worker-startup", ["docker", "run", "-d", "--name", worker, *connection,
                               image, "python", "-m", "app.worker"])
        run("readiness", [sys.executable, "scripts/wait_http.py", "--timeout", "45",
                          environment["API_URL"] + "/health", environment["FRONTEND_URL"]], timeout=60)
        run("runtime-config", ["docker", "exec", container, "python", "-c",
            "import json,os,shutil; from app.core.config import get_settings; "
            "print(json.dumps({'uid':os.getuid(),'node':shutil.which('node'),"
            "'npm':shutil.which('npm'),'environment':get_settings().environment}))"])
        npx = "npx.cmd" if os.name == "nt" else "npx"
        run("browser", [npx, "playwright", "test", "--project=chromium", "--reporter=line,json",
                        "--trace=retain-on-failure", f"--output={output / 'browser'}"],
            cwd=ROOT / "frontend", timeout=600)
        run("runtime", ["docker", "logs", container])
        run("worker-state", ["docker", "inspect", "--format", "{{.State.Running}}", worker])
        if (output / "worker-state.log").read_text(encoding="utf-8").strip() != "true":
            raise RuntimeError("Compiled worker exited during browser verification")
        run("worker-runtime", ["docker", "logs", worker])
        config = json.loads((output / "runtime-config.log").read_text(encoding="utf-8"))
        summary = inspect_runtime(config, (output / "runtime.log").read_text(encoding="utf-8"))
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    finally:
        run("final-runtime", ["docker", "logs", container], required=False)
        run("final-worker-runtime", ["docker", "logs", worker], required=False)
        # Names are generated in this invocation; never remove stack services or volumes.
        migration_cleanup = run("cleanup-migration", ["docker", "rm", "-f", migration], required=False)
        cleanup = run("cleanup", ["docker", "rm", "-f", container], required=False)
        worker_cleanup = run("cleanup-worker", ["docker", "rm", "-f", worker], required=False)
    if cleanup or migration_cleanup or worker_cleanup:
        raise RuntimeError(f"Probe cleanup failed; inspect {output}")
    print(f"Built web verification passed: {output}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("asi-verification", "asi-ci"), default="asi-verification")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    verify(args.project, args.port)
