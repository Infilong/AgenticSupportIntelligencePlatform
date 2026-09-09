"""Run real PostgreSQL tests in temporary schemas of a dedicated rebuild test database."""
import os
import shutil
import subprocess
import uuid

from evidence import run_checked
from runtime import ROOT


def main(capacity=False):
    uv = shutil.which("uv")
    if not uv or not (ROOT / ".env").is_file():
        print("Run init-env/up and install uv before integration checks.")
        return 1
    owner = subprocess.check_output([
        "docker", "inspect", "asi-rebuild-v1-postgres-1", "--format",
        '{{index .Config.Labels "com.docker.compose.project"}} {{.State.Running}}',
    ], text=True).strip()
    if owner != "asi-rebuild-v1 true":
        raise RuntimeError("Expected the running isolated rebuild database")
    psql = ["docker", "exec", "asi-rebuild-v1-postgres-1", "psql", "-U", "asi_rebuild", "-d", "postgres"]
    exists = subprocess.check_output([*psql, "-tAc", "SELECT 1 FROM pg_database WHERE datname='asi_rebuild_test'"],
                                     text=True).strip()
    if not exists:
        subprocess.run([*psql, "-v", "ON_ERROR_STOP=1", "-c", "CREATE DATABASE asi_rebuild_test"], check=True)
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text().splitlines()
                  if "=" in line and not line.startswith("#"))
    # init-env creates URL-safe credentials; do not put them in process arguments or reports.
    from urllib.parse import quote
    password = quote(values["ASI_DATABASE_PASSWORD"], safe="")
    port = int(values.get("ASI_DATABASE_PORT", "5440"))
    env = {**os.environ, "ASI_TEST_DATABASE_URL":
           f"postgresql+psycopg://asi_rebuild:{password}@127.0.0.1:{port}/asi_rebuild_test"}
    targets = ["tests/integration"]
    if capacity:
        targets = ["tests/integration/test_inbox_capacity.py", "tests/integration/test_message_capacity.py",
                   "tests/integration/test_inbox_views.py"]
        env.update({"ASI_CAPACITY_BROWSER": "1", "ASI_CAPACITY_BUDGET_MS": "1000"})
    # A fresh workspace-owned directory avoids shared Windows pytest temp ownership conflicts.
    temporary = ROOT / ".artifacts" / "m0" / f"pytest-integration-{uuid.uuid4().hex}"
    return run_checked("inbox-capacity" if capacity else "integration",
                       [uv, "run", "--frozen", "pytest", *targets, "-q", "--tb=short",
                        "--basetemp", str(temporary)], ROOT / "backend", env, timeout=420)


if __name__ == "__main__":
    raise SystemExit(main())
