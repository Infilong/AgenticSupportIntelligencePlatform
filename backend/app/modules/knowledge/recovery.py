"""Retrieval ownership and bounded recovery; absence of ownership is not proof CPU work stopped."""

import hashlib
import uuid

import psycopg
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.jobs.contracts import RetryableJobError
from app.modules.knowledge.retrieval_models import RetrievalTrace
from app.modules.usage.models import ModelCall


class RetrievalOwnershipLost(RetryableJobError):
    pass


def lock_key(trace_id):
    value = hashlib.blake2b(b"asi:retrieval:" + trace_id.bytes, digest_size=8).digest()
    return int.from_bytes(value, "big", signed=True)


class RetrievalOwner:
    def __init__(self, engine):
        self.engine = engine
        self.trace_id = uuid.uuid4()
        self.connection = None

    def __enter__(self):
        url = self.engine.url
        try:
            options = dict(url.query)
            options["options"] = options.get("options", "") + " -c statement_timeout=5000"
            self.connection = psycopg.connect(
                **url.translate_connect_args(username="user", database="dbname"),
                **options,
                autocommit=True,
                connect_timeout=3,
                keepalives_idle=5,
                keepalives_interval=2,
                keepalives_count=3,
                tcp_user_timeout=10000,
            )
            locked = self.connection.execute(
                "SELECT pg_try_advisory_lock(%s)", (lock_key(self.trace_id),)
            ).fetchone()[0]
            if not locked:
                raise RetrievalOwnershipLost("Retrieval ownership unavailable")
            return self
        except (psycopg.OperationalError, psycopg.InterfaceError) as error:
            if self.connection is not None:
                self.connection.close()
            raise RetrievalOwnershipLost("Retrieval ownership connection unavailable") from error
        except Exception:
            if self.connection is not None:
                self.connection.close()
            raise

    def __exit__(self, *_):
        self.connection.close()  # Dedicated session: never return an advisory lock to a pool.

    def check(self, db):
        try:
            self.connection.execute("SELECT 1").fetchone()
        except (psycopg.OperationalError, psycopg.InterfaceError) as error:
            raise RetrievalOwnershipLost("Retrieval ownership lost") from error
        trace = db.scalar(
            select(RetrievalTrace)
            .where(
                RetrievalTrace.id == self.trace_id,
            )
            .with_for_update()
        )
        if trace is None or trace.status != "started":
            raise RetrievalOwnershipLost("Retrieval no longer accepts writes")
        return trace


def reconcile(engine, after=None, limit=50):
    """Return a fair keyset cursor and count; one bounded batch, no user-facing data reads."""
    if not 1 <= limit <= 100:
        raise ValueError("Recovery batch must contain 1–100 records")
    with Session(engine) as db, db.begin():
        query = select(RetrievalTrace.id).where(RetrievalTrace.status == "started")
        if after is not None:
            query = query.where(RetrievalTrace.id > after)
        ids = list(db.scalars(query.order_by(RetrievalTrace.id).limit(limit)))
        repaired = 0
        for trace_id in ids:
            if not db.scalar(text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": lock_key(trace_id)}):
                continue
            trace = db.scalar(
                select(RetrievalTrace)
                .where(
                    RetrievalTrace.id == trace_id,
                    RetrievalTrace.status == "started",
                )
                .with_for_update(skip_locked=True)
            )
            if trace is None:
                continue
            trace.status, trace.error_code = "uncertain", "retrieval_ownership_lost"
            db.execute(
                update(ModelCall)
                .where(
                    ModelCall.workspace_id == trace.workspace_id,
                    ModelCall.retrieval_id == trace.id,
                    ModelCall.status == "started",
                )
                .values(status="uncertain", error_code="retrieval_ownership_lost")
            )
            repaired += 1
        return (ids[-1] if len(ids) == limit else None), repaired
