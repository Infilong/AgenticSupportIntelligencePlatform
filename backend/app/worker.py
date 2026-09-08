"""Single-job worker; handlers run outside transactions and publish under a fenced lease."""

import json
import logging
import signal
import sys
import threading
import time
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.engine import make_engine
from app.jobs.queue import LeaseLost, authorize, claim, finish, heartbeat, owned
from app.modules.identity import models as identity_models  # noqa: F401

LOG = logging.getLogger("asi.worker")
HEALTH = Path("/tmp/asi-worker-heartbeat")


def diagnostic(engine, job):
    with engine.connect() as connection:
        version = connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    return {"database": "reachable", "vector_version": version, "schema_revision": revision}


HANDLERS = {"database_check": diagnostic}


def run_once(engine, handlers=None, health_callback=lambda: None):
    with Session(engine, expire_on_commit=False) as db, db.begin():
        job = claim(db)
    health_callback()
    if job is None:
        return False
    started = time.monotonic()
    stopped = threading.Event()

    def keep_alive():
        while not stopped.wait(15):
            try:
                with Session(engine) as db, db.begin():
                    active = heartbeat(db, job.id, job.lease_token)
                health_callback()
                if not active:
                    return
            except (LeaseLost, SQLAlchemyError):
                return  # Publication still requires a live lease; never substitute a new token.

    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
    outcome = "failed"
    try:
        with Session(engine) as db, db.begin():
            authorize(db, job.workspace_id, job.actor_id)
            if owned(db, job.id, job.lease_token).cancel_requested:
                outcome = finish(db, job.id, job.lease_token).state
                return True
        handler = (handlers if handlers is not None else HANDLERS).get(job.kind)
        if handler is None:
            raise ValueError("Unsupported job kind")
        result = handler(engine, job)
        with Session(engine) as db, db.begin():
            authorize(db, job.workspace_id, job.actor_id)
            outcome = finish(db, job.id, job.lease_token, result=result).state
    except LeaseLost:
        outcome = "lease_lost"
    except Exception as error:
        # Worker boundary: persist explicit failure; never log payload, credentials or raw errors.
        code = "actor_access_revoked" if isinstance(error, HTTPException) else type(error).__name__[:64]
        try:
            with Session(engine) as db, db.begin():
                outcome = finish(
                    db, job.id, job.lease_token, error_code=code, retry=isinstance(error, SQLAlchemyError)
                ).state
        except (LeaseLost, SQLAlchemyError):
            outcome = "unconfirmed_failure"  # Lease recovery owns the next attempt.
    finally:
        stopped.set()
        thread.join(timeout=6)
        LOG.info(
            json.dumps(
                {
                    "event": "job_finished",
                    "job_id": str(job.id),
                    "workspace_id": str(job.workspace_id),
                    "kind": job.kind,
                    "attempt": job.attempts,
                    "outcome": outcome,
                    "duration_ms": round((time.monotonic() - started) * 1000, 2),
                }
            )
        )
    return True


def main():
    if "--health" in sys.argv:
        return 0 if HEALTH.exists() and time.time() - HEALTH.stat().st_mtime < 30 else 1
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    engine = make_engine(Settings())
    stop = threading.Event()
    for name in (signal.SIGTERM, signal.SIGINT):
        signal.signal(name, lambda *_: stop.set())
    try:
        while not stop.is_set():
            try:
                worked = run_once(engine, health_callback=HEALTH.touch)
            except SQLAlchemyError:
                LOG.error(json.dumps({"event": "worker_database_unavailable"}))
                worked = False
            if not worked:
                stop.wait(2)
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
