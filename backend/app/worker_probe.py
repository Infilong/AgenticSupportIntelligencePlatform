"""Submit a real diagnostic job and observe the separate worker's persisted result."""

import json
import time
import uuid

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.db.engine import make_engine
from app.jobs.models import Job
from app.jobs.queue import enqueue
from app.modules.identity.models import User
from app.modules.workspaces.models import Membership


def main():
    settings = Settings()
    if make_url(settings.database_url.get_secret_value()).database != "asi_rebuild":
        raise ValueError("Runtime probe requires the isolated rebuild database")
    engine = make_engine(settings)
    try:
        with Session(engine, expire_on_commit=False) as db, db.begin():
            actor = db.scalar(select(User).where(User.email == "admin@asterworks.example"))
            if actor is None:
                raise ValueError("Run seed-demo before the worker probe")
            member = db.scalar(
                select(Membership).where(Membership.user_id == actor.id, Membership.role == "admin")
            )
            if member is None:
                raise ValueError("Demo administrator no longer has workspace access")
            job = enqueue(db, member.workspace_id, actor.id, "database_check", uuid.uuid4().hex, {})
            job_id = job.id
        for _ in range(30):
            with Session(engine) as db:
                job = db.get(Job, job_id)
                if job.state in {"succeeded", "failed", "cancelled"}:
                    print(
                        json.dumps(
                            {
                                "job_id": str(job.id),
                                "state": job.state,
                                "attempts": job.attempts,
                                "result": job.result,
                                "error_code": job.error_code,
                            }
                        )
                    )
                    return 0 if job.state == "succeeded" and job.result["vector_version"] else 1
            time.sleep(1)
        print(json.dumps({"job_id": str(job_id), "state": "verification_timeout"}))
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
