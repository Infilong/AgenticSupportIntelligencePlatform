"""Scheduling primitives; callers own transactions and domain publication."""

import hashlib
import json
import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from app.jobs.models import Job
from app.modules.usage.models import ModelCall
from app.modules.workspaces.models import Workspace
from app.modules.workspaces.service import membership

LEASE_SECONDS = 60


class LeaseLost(Exception):
    pass


class JobCancelled(Exception):
    pass


def authorize(db, workspace_id, actor_id):
    # Membership mutations use this same workspace-first lock order.
    workspace = db.scalar(select(Workspace).where(Workspace.id == workspace_id).with_for_update())
    if workspace is None:
        raise HTTPException(404, "Workspace unavailable")
    membership(db, workspace_id, actor_id, {"admin", "operator"})


def enqueue(db, workspace_id, actor_id, kind, key, payload, priority=10):
    authorize(db, workspace_id, actor_id)
    serialized = json.dumps(
        {"actor": str(actor_id), "kind": kind, "payload": payload},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if not key or len(key) > 100 or len(serialized.encode()) > 16384:
        raise ValueError("Job key or payload exceeds limits")
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    job_id = db.execute(
        insert(Job)
        .values(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            actor_id=actor_id,
            kind=kind,
            idempotency_key=key,
            payload_hash=digest,
            payload=payload,
            priority=priority,
            state="queued",
            attempts=0,
            max_attempts=3,
            cancel_requested=False,
        )
        .on_conflict_do_nothing(constraint="uq_job_key")
        .returning(Job.id)
    ).scalar_one_or_none()
    job = (
        db.get(Job, job_id)
        if job_id
        else db.scalar(select(Job).where(Job.workspace_id == workspace_id, Job.idempotency_key == key))
    )
    if job.payload_hash != digest:
        raise HTTPException(409, "This submission key already belongs to different input")
    return job


def claim(db):
    # SKIP LOCKED lets concurrent workers claim different rows without sharing a lease.
    job = db.scalar(
        select(Job)
        .where(
            or_(
                (Job.state == "queued") & (Job.available_at <= func.clock_timestamp()),
                (Job.state == "running") & (Job.lease_expires_at <= func.clock_timestamp()),
            )
        )
        .order_by(Job.priority, Job.available_at, Job.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if job is None:
        return None
    if job.attempts:
        db.execute(
            update(ModelCall)
            .where(ModelCall.job_id == job.id, ModelCall.status == "started")
            .values(status="uncertain")
        )
    if job.cancel_requested or job.attempts >= job.max_attempts:
        job.state = "cancelled" if job.cancel_requested else "failed"
        job.error_code = None if job.cancel_requested else "lease_attempts_exhausted"
        job.finished_at = db.scalar(select(func.clock_timestamp()))
        job.lease_token = None
        job.lease_expires_at = None
        return None
    job.state = "running"
    job.attempts += 1
    job.lease_token = uuid.uuid4()
    job.heartbeat_at = db.scalar(select(func.clock_timestamp()))
    job.lease_expires_at = job.heartbeat_at + timedelta(seconds=LEASE_SECONDS)
    job.error_code = None
    db.flush()
    return job


def owned(db, job_id, token):
    job = db.scalar(
        select(Job)
        .where(
            Job.id == job_id,
            Job.state == "running",
            Job.lease_token == token,
            Job.lease_expires_at > func.clock_timestamp(),
        )
        .with_for_update()
    )
    if job is None:
        raise LeaseLost()
    return job


def heartbeat(db, job_id, token):
    job = owned(db, job_id, token)
    if job.cancel_requested:
        return False
    job.heartbeat_at = db.scalar(select(func.clock_timestamp()))
    job.lease_expires_at = job.heartbeat_at + timedelta(seconds=LEASE_SECONDS)
    return True


def finish(db, job_id, token, result=None, error_code=None, retry=False):
    job = owned(db, job_id, token)
    current_time = db.scalar(select(func.clock_timestamp()))
    if job.cancel_requested:
        job.state = "cancelled"
    elif error_code and retry and job.attempts < job.max_attempts:
        job.state = "queued"
        job.available_at = current_time + timedelta(seconds=min(60, 2**job.attempts))
    else:
        job.state = "failed" if error_code else "succeeded"
        job.result = result if not error_code else None
    job.error_code = error_code
    job.lease_token = None
    job.lease_expires_at = None
    job.finished_at = None if job.state == "queued" else current_time
    return job


def request_cancel(db, workspace_id, actor_id, job_id):
    authorize(db, workspace_id, actor_id)
    job = db.scalar(select(Job).where(Job.workspace_id == workspace_id, Job.id == job_id).with_for_update())
    if job is None:
        raise HTTPException(404, "Job unavailable")
    if job.state in {"queued", "running"}:
        job.cancel_requested = True
        if job.state == "queued":
            job.state = "cancelled"
            job.finished_at = db.scalar(select(func.clock_timestamp()))
    return job
