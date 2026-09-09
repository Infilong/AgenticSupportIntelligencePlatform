"""Synthetic stored states for isolated database capacity checks, never AI execution proof."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, text
from sqlalchemy.orm import Session

from app.jobs.models import Job
from app.modules.support.models import Message, SupportRun

STATES = [
    ("completed", "approved_response", "succeeded", "ready"),
    ("waiting_for_input", None, "succeeded", "attention"),
    ("awaiting_review", "grounded_draft", "succeeded", "attention"),
    ("completed", "clarification_needed", "succeeded", "attention"),
    ("queued", None, "queued", "processing"),
    ("queued", None, "failed", "failed"),
    ("cancelled", None, "cancelled", "all"),
    ("rejected", "rejected_response", "succeeded", "all"),
]


def seed_capacity(engine, workspace_id, actor_id, count=50000, prefix="CAP"):
    if engine.url.database != "asi_rebuild_test":
        raise ValueError("Capacity fixtures require the dedicated test database")
    expected = []
    with Session(engine) as db, db.begin():
        schema = db.scalar(text("SELECT current_schema()"))
        if not schema.startswith("test_"):
            raise ValueError("Capacity fixtures require an isolated test schema")
        for start in range(0, count, 2000):
            messages, jobs, runs, children = [], [], [], []
            for index in range(start, min(count, start + 2000)):
                message_id = uuid.uuid5(workspace_id, f"{prefix}:message:{index}")
                run_id = uuid.uuid5(message_id, "run:1")
                job_id = uuid.uuid5(run_id, "job")
                language, phrase = [("en", "refund policy"), ("ja", "返金ポリシー"), ("zh", "退款政策")][
                    index % 3
                ]
                original = f"Synthetic {prefix}-{index:05d} {phrase}"
                created = datetime(2026, 9, 1, tzinfo=UTC) + timedelta(seconds=index // 5)
                state, outcome, job_state, view = STATES[index % len(STATES)]
                messages.append(
                    dict(
                        id=message_id,
                        workspace_id=workspace_id,
                        actor_id=actor_id,
                        original=original,
                        language=language,
                        submission_key=f"{prefix}:{index}",
                        input_hash="0" * 64,
                        created_at=created,
                    )
                )
                job = dict(
                    id=job_id,
                    workspace_id=workspace_id,
                    actor_id=actor_id,
                    kind="support_run",
                    idempotency_key=f"capacity:{run_id}",
                    payload_hash="0" * 64,
                    payload={},
                    state=job_state,
                    available_at=datetime(2099, 1, 1, tzinfo=UTC),
                )
                run = dict(
                    id=run_id,
                    workspace_id=workspace_id,
                    message_id=message_id,
                    job_id=job_id,
                    creator_id=actor_id,
                    input_text=original,
                    state=state,
                    outcome=outcome,
                )
                jobs.append(job)
                runs.append(run)
                # A newer failed attempt must replace the older outcome, not duplicate the message.
                if index % 100 == 0:
                    child_id = uuid.uuid5(message_id, "run:2")
                    child_job = uuid.uuid5(child_id, "job")
                    jobs.append(
                        {**job, "id": child_job, "idempotency_key": f"capacity:{child_id}", "state": "failed"}
                    )
                    children.append(
                        {
                            **run,
                            "id": child_id,
                            "job_id": child_job,
                            "state": "queued",
                            "outcome": None,
                            "attempt_number": 2,
                            "attempt_kind": "retry",
                            "parent_run_id": run_id,
                        }
                    )
                    run_id, view = child_id, "failed"
                expected.append(
                    dict(
                        id=str(message_id),
                        run_id=str(run_id),
                        view=view,
                        original=original,
                        created_at=created,
                    )
                )
            db.execute(insert(Message), messages)
            db.execute(insert(Job), jobs)
            db.execute(insert(SupportRun), runs)
            if children:
                db.execute(insert(SupportRun), children)
        for table in ("support_messages", "support_runs", "jobs"):
            db.execute(text(f"ANALYZE {table}"))
    return sorted(expected, key=lambda item: (-item["created_at"].timestamp(), item["id"]))
