"""Logical restore drill for synthetic asi-verification data, never the application database."""

import json
from pathlib import Path
import subprocess
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BASE = ["docker", "compose", "-p", "asi-verification", "exec", "-T", "postgres"]
SOURCE = "agentic_support"


def run(arguments, *, stdin=None, stdout=subprocess.PIPE):
    result = subprocess.run(BASE + arguments, cwd=ROOT, input=stdin, stdout=stdout,
                            stderr=subprocess.PIPE, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


def manifest(database):
    sql = (ROOT / "scripts/recovery_manifest.sql").read_bytes()
    output = run(["psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
                  "-U", "agentic", "-d", database], stdin=sql)
    rows = []
    for line in output.decode("utf-8").splitlines():
        table, count, fingerprint = line.split("|")
        rows.append({"table": table, "rows": int(count), "hash": fingerprint})
    if not rows or not any(row["table"] == "alembic_version" for row in rows):
        raise RuntimeError("Source must contain an initialized application schema.")
    return rows


def probe_application(target, artifacts):
    command = ["docker", "compose", "-p", "asi-verification", "run", "--rm", "-T",
               "--no-deps", "-e", "DATABASE_URL=postgresql+psycopg://agentic:agentic@postgres:5432/" + target,
               "-e", "EMBEDDING_PROVIDER=mock", "-e", "OPENAI_API_KEY=",
               "-v", str(ROOT / "scripts") + ":/recovery:ro",
               "-v", str(ROOT / "backend/app") + ":/app/app:ro",
               "api", "uv", "run", "--frozen", "--extra", "dev", "python",
               "/recovery/probe_restored_application.py"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=180)
    (artifacts / "application.log").write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("Restored API probe failed; inspect application.log")
    return json.loads(result.stdout.decode("utf-8").splitlines()[-1])


def main():
    identifier = uuid4().hex
    target = "asi_restore_" + identifier
    artifacts = ROOT / ".artifacts" / ("database-restore-" + identifier)
    artifacts.mkdir(parents=True)
    archive = artifacts / "database.dump"
    report = {"source": SOURCE, "target": target, "project": "asi-verification",
              "status": "running", "cleanup": "not_created"}
    created = False
    started = time.monotonic()
    try:
        before = manifest(SOURCE)
        report["source_tables"] = before
        with archive.open("wb") as output:
            run(["pg_dump", "-U", "agentic", "-d", SOURCE, "--format=custom",
                 "--no-owner", "--no-acl"], stdout=output)
        if manifest(SOURCE) != before:
            raise RuntimeError("Source changed during backup; repeat during a quiet window.")
        run(["createdb", "-U", "agentic", "--template=template0", target])
        created = True
        # Pass bytes directly: PowerShell text redirection can corrupt custom-format dumps.
        run(["pg_restore", "-U", "agentic", "--dbname=" + target,
             "--exit-on-error", "--single-transaction", "--no-owner", "--no-acl"],
            stdin=archive.read_bytes())
        restored = manifest(target)
        report["restored_tables"] = restored
        if restored != before:
            raise RuntimeError("Restored table counts/content differ from the source manifest.")
        if manifest(SOURCE) != before:
            raise RuntimeError("Source changed during restore; comparison needs a quiet window.")
        revision = run(["psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1",
                        "-U", "agentic", "-d", target, "-c",
                        "SELECT version_num FROM alembic_version ORDER BY version_num"])
        report["application"] = probe_application(target, artifacts)
        if manifest(SOURCE) != before:
            raise RuntimeError("Source changed during application probe.")
        report.update(status="passed", revision=revision.decode().strip(),
                      archive_bytes=archive.stat().st_size)
    except Exception as exc:
        report.update(status="failed", error=str(exc))
        raise
    finally:
        try:
            if created:
                # Name is generated here; no CLI/user input can select a cleanup target.
                run(["dropdb", "-U", "agentic", target])
                report["cleanup"] = "dropped_created_target"
        except Exception as exc:
            report.update(status="failed", cleanup="failed", cleanup_error=str(exc))
            raise
        finally:
            report["elapsed_seconds"] = round(time.monotonic() - started, 3)
            (artifacts / "report.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"Restore drill {report['status']}: {artifacts / 'report.json'}")


if __name__ == "__main__":
    main()
