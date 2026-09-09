"""Export a fresh snapshot; optionally verify it in a new disposable database."""
import argparse
import hashlib
import json
import re
import secrets
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
CONTAINER = "asi-rebuild-v1-postgres-1"
DEADLINE = time.monotonic() + 180
CONNECT = {"connect_timeout": 5, "options": "-c statement_timeout=10000 -c lock_timeout=3000"}


def remaining():
    seconds = DEADLINE - time.monotonic()
    if seconds <= 0:
        raise TimeoutError("Restoration drill internal deadline exceeded")
    return seconds


def docker(*arguments, **options):
    return subprocess.run(["docker", *arguments], check=True, timeout=min(60, remaining()), **options)


def fingerprints(connection):
    tables = connection.scalars(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )).all()
    result = {}
    for table in tables:
        remaining()
        quoted = connection.dialect.identifier_preparer.quote(table)
        digest, count = hashlib.sha256(), 0
        rows = connection.execute(text(f"SELECT to_jsonb(t)::text AS body FROM public.{quoted} t ORDER BY body"))
        for row in rows:
            digest.update(row.body.encode("utf-8") + b"\n")
            count += 1
        result[table] = {"rows": count, "sha256": digest.hexdigest()}
    return result


def metadata(connection):
    sequences = []
    for name in connection.scalars(text("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")):
        quoted = connection.dialect.identifier_preparer.quote(name)
        values = connection.execute(text(f"SELECT last_value, is_called FROM public.{quoted}")).mappings().one()
        sequences.append({"name": name, **dict(values)})
    return {
        "extensions": [dict(row) for row in connection.execute(text(
            "SELECT extname, extversion FROM pg_extension ORDER BY extname")).mappings()],
        "sequences": sequences,
    }


def exercise(url, report, engine):
    # Login and worker execution happen only after clone fingerprints match the backup snapshot.
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session

    from app.core.settings import Settings
    from app.main import create_app
    from app.modules.identity.models import User
    from app.modules.identity.security import passwords
    from app.modules.workspaces.models import Membership, Workspace
    from app.worker import run_once

    password = secrets.token_urlsafe(24)
    user_id, workspace_id = uuid.uuid4(), uuid.uuid4()
    email = f"restore-{user_id.hex}@example.invalid"
    with Session(engine) as db, db.begin():
        # Quiesce inherited active jobs in the disposable clone only. Never execute old actions.
        result = db.execute(text("UPDATE jobs SET state='cancelled', cancel_requested=true "
                                 "WHERE state IN ('queued','running')"))
        report["inherited_jobs_quiesced"] = result.rowcount
        db.add(User(id=user_id, email=email, display_name="Restoration proof", password_hash=passwords.hash(password)))
        db.add(Workspace(id=workspace_id, name="Disposable restoration proof"))
        db.flush()
        db.add(Membership(workspace_id=workspace_id, user_id=user_id, role="admin"))
    with TestClient(create_app(Settings(database_url=url)), base_url="http://127.0.0.1:8010") as client:
        assert client.get("/api/health/ready").status_code == 200
        token = client.get("/api/session").json()["csrf_token"]
        headers = {"Origin": "http://127.0.0.1:8010", "X-CSRF-Token": token}
        logged = client.post("/api/session/login", headers=headers, json={"email": email, "password": password})
        assert logged.status_code == 200
        headers["X-CSRF-Token"] = logged.json()["csrf_token"]
        response = client.post(f"/api/workspaces/{workspace_id}/messages", headers={**headers, "Idempotency-Key": "restore-proof"},
                               json={"original": "w", "language": "en"})
        assert response.status_code == 202, response.status_code
        ids = response.json()
        deadline = time.monotonic() + 10
        while not run_once(engine):
            if time.monotonic() >= deadline:
                raise RuntimeError("Restored worker did not claim the new request")
            time.sleep(0.1)
        path = f"/api/workspaces/{workspace_id}/runs/{ids['run_id']}"
        result = client.get(path)
        assert result.status_code == 200
        run = result.json()
        assert run["state"] == "completed" and run["outcome"] == "clarification_needed"
        assert run["retrieval_id"] is None and not run["model_calls"]
        report["new_request"] = {**ids, "state": run["state"], "outcome": run["outcome"], "model_calls": 0}
        assert client.get(f"/api/workspaces/{workspace_id}/messages").json()["total"] == 1
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT state FROM jobs WHERE id=:id"), {"id": ids["job_id"]}) == "succeeded"
            checkpoints = connection.scalar(text("SELECT count(*) FROM checkpoints WHERE thread_id=:thread"),
                {"thread": f"support:{workspace_id}:{ids['run_id']}"})
            assert checkpoints > 0
            report["new_request"]["checkpoint_count"] = checkpoints


def main(*, backup_only=False, backup_dir=None):
    if backup_only and backup_dir is not None:
        raise ValueError("Backup export cannot also restore a saved backup")
    identity = docker("inspect", CONTAINER, "--format",
        '{{index .Config.Labels "com.docker.compose.project"}} {{.State.Running}}', capture_output=True, text=True).stdout.strip()
    if identity != "asi-rebuild-v1 true":
        raise RuntimeError("Expected the running isolated rebuild PostgreSQL container")
    target = "asi_restore_" + uuid.uuid4().hex[:12]
    if not re.fullmatch(r"asi_restore_[a-f0-9]{12}", target):
        raise ValueError("Refusing a non-disposable restoration target")
    mode = "backup" if backup_only else "restore-saved" if backup_dir is not None else "restore"
    directory = ROOT / ".artifacts" / "m6" / (mode + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    directory.mkdir(parents=True, exist_ok=False)
    dump = directory / "snapshot.dump"
    report = {"status": "started", "source_database": "asi_rebuild"}
    if backup_only:
        report.update(scope="database snapshot export only; restoration not attempted",
                      restoration_verified=False)
    else:
        report.update(target_database=target,
                      scope=("saved backup parity and restored API/worker clarification; no generation/RAG quality claim"
                             if backup_dir is not None else
                             "fresh snapshot parity and restored API/worker clarification; no generation/RAG quality claim"))
    values = dict(line.split("=", 1) for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
                  if "=" in line and not line.startswith("#"))
    prefix = f"postgresql+psycopg://asi_rebuild:{quote(values['ASI_DATABASE_PASSWORD'], safe='')}@127.0.0.1:{int(values.get('ASI_DATABASE_PORT', '5440'))}/"
    source = None
    clone = None
    try:
        if backup_dir is not None:
            from backup_archive import copy_verified_backup
            report.update(copy_verified_backup(ROOT, Path(backup_dir), dump, remaining))
        else:
            source = create_engine(prefix + "asi_rebuild", hide_parameters=True, connect_args=CONNECT)
            with source.connect().execution_options(isolation_level="REPEATABLE READ") as connection, connection.begin():
                connection.execute(text("SET TRANSACTION READ ONLY"))
                connection.execute(text("SET TIME ZONE 'UTC'"))
                snapshot = connection.scalar(text("SELECT pg_export_snapshot()"))
                report["snapshot"] = snapshot
                report["source_tables"] = fingerprints(connection)
                report["source_metadata"] = metadata(connection)
                with dump.open("wb") as output:
                    docker("exec", CONTAINER, "pg_dump", "-U", "asi_rebuild", "-d", "asi_rebuild",
                           "-Fc", "--no-owner", "--snapshot", snapshot, stdout=output)
            with dump.open("rb") as original:
                report["dump_sha256"] = hashlib.file_digest(original, "sha256").hexdigest()
            report["dump_bytes"] = dump.stat().st_size
        if report["dump_bytes"] == 0:
            raise RuntimeError("Database export produced an empty archive")
        if backup_only:
            report["status"] = "passed"
            return 0
        # createdb fails if a target already exists. No --clean, overwrite or drop operation exists.
        docker("exec", CONTAINER, "createdb", "-U", "asi_rebuild", target)
        report["database_created"] = True
        with dump.open("rb") as original:
            docker("exec", "-i", CONTAINER, "pg_restore", "-U", "asi_rebuild", "-d", target,
                   "--no-owner", "--exit-on-error", stdin=original)
        clone = create_engine(prefix + target, hide_parameters=True, connect_args=CONNECT)
        with clone.connect() as connection:
            connection.execute(text("SET TIME ZONE 'UTC'"))
            report["restored_tables"] = fingerprints(connection)
            report["restored_metadata"] = metadata(connection)
        assert report["source_tables"] == report["restored_tables"], "Restored table fingerprints differ"
        assert report["source_metadata"] == report["restored_metadata"], "Extension/sequence metadata differs"
        report["parity_verified"] = True
        exercise(prefix + target, report, clone)
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error_type"] = type(error).__name__
        raise
    finally:
        if source is not None:
            source.dispose()
        if clone is not None:
            clone.dispose()
        (directory / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if backup_only:
            print(f"Backup evidence: {directory}; restoration not attempted")
        else:
            print(f"Restoration evidence: {directory}; disposable target: {target} (created={report.get('database_created', False)})")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--backup-only", action="store_true", help="Export without creating or exercising a restore database")
    mode.add_argument("--backup-dir", type=Path, help="Restore a trusted local standalone backup instead of a fresh export")
    args = parser.parse_args()
    raise SystemExit(main(backup_only=args.backup_only, backup_dir=args.backup_dir))
