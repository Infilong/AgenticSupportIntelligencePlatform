"""PostgreSQL execution ownership; callers must finalize through the owned connection."""

import hashlib
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ExecutionBusy(RuntimeError):
    pass


class ExecutionOwnershipLost(RuntimeError):
    pass


@dataclass(frozen=True)
class ExecutionOwner:
    connection: Connection
    workspace_id: UUID
    execution_id: UUID
    backend_pid: int
    key_a: int
    key_b: int

    def assert_owned(self) -> None:
        # A reconnect is a different owner, even if it could acquire the same lock later.
        if self.connection.closed or self.connection.invalidated:
            raise ExecutionOwnershipLost("provider_execution_ownership_lost")
        owned = self.connection.scalar(text(
            "SELECT pg_backend_pid() = :pid AND EXISTS (SELECT 1 FROM pg_locks "
            "WHERE locktype = 'advisory' AND pid = pg_backend_pid() AND granted "
            "AND classid = :a AND objid = :b AND objsubid = 2)"
        ), {"pid": self.backend_pid, "a": self.key_a, "b": self.key_b})
        if not owned:
            raise ExecutionOwnershipLost("provider_execution_ownership_lost")


@contextmanager
def own_execution(engine: Engine, *, workspace_id: UUID, execution_id: UUID):
    if not isinstance(engine, Engine) or engine.dialect.name != "postgresql":
        raise ValueError("Execution ownership requires a PostgreSQL engine")
    digest = hashlib.sha256(workspace_id.bytes + execution_id.bytes).digest()
    # Positive int32 keys fit PostgreSQL's two-key advisory namespace. Hash collisions can
    # conservatively block unrelated work; they cannot grant two owners the same execution.
    a = int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
    b = int.from_bytes(digest[4:8], "big") & 0x7FFFFFFF
    with engine.connect() as connection:
        acquired = False
        try:
            acquired = connection.scalar(text("SELECT pg_try_advisory_lock(:a, :b)"),
                                         {"a": a, "b": b})
            if not acquired:
                raise ExecutionBusy("provider_execution_busy")
            pid = connection.scalar(text("SELECT pg_backend_pid()"))
            connection.commit()  # Session lock survives; no idle transaction during provider I/O.
            yield ExecutionOwner(connection, workspace_id, execution_id, pid, a, b)
        finally:
            if acquired and not connection.invalidated and not connection.closed:
                try:
                    connection.rollback()
                    released = connection.scalar(text("SELECT pg_advisory_unlock(:a, :b)"),
                                                  {"a": a, "b": b})
                    connection.commit()
                    if not released:
                        connection.invalidate()
                except SQLAlchemyError as error:
                    # Never return a pooled session with an unverified retained advisory lock.
                    connection.invalidate()
                    logger.warning("execution_owner_cleanup_failed error_type=%s",
                                   type(error).__name__)
