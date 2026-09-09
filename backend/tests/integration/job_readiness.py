"""Wait for observed initial-job availability; never retry execution or alter scheduling."""

import json
import os
import time
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.jobs.models import Job


def wait_initial(system, kind, max_wait=5):
    started = time.monotonic()
    first = None
    while True:
        with Session(system["engine"]) as db:
            row = db.execute(
                select(Job.id, Job.available_at)
                .where(
                    Job.workspace_id == system["workspace"],
                    Job.kind == kind,
                    Job.state == "queued",
                    Job.attempts == 0,
                    Job.cancel_requested.is_(False),
                )
                .order_by(Job.available_at, Job.id)
                .limit(1)
            ).first()
            now = db.scalar(select(func.clock_timestamp()))
        # Every observation transaction is closed before any wait.
        if row is None or row.available_at <= now:
            if first is not None:
                event = {
                    **first,
                    "waited_ms": round((time.monotonic() - started) * 1000, 2),
                    "ready_database_time": str(now),
                }
                system.setdefault("job_readiness", []).append(event)
                directory = os.environ.get("ASI_EVIDENCE_DIR")
                if directory:
                    with (Path(directory) / "job-readiness.jsonl").open("a", encoding="utf-8") as output:
                        output.write(json.dumps(event) + "\n")
            return row is not None
        first = first or {
            "job_id": str(row.id),
            "kind": kind,
            "available_at": str(row.available_at),
            "observed_database_time": str(now),
        }
        remaining = max_wait - (time.monotonic() - started)
        assert remaining > 0, {**first, "last_database_time": str(now), "deadline_seconds": max_wait}
        time.sleep(min(0.1, remaining, (row.available_at - now).total_seconds()))
