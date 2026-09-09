import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    __tablename__ = "support_messages"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_message_workspace"),
        UniqueConstraint("workspace_id", "submission_key", name="uq_message_submission"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    original: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    submission_key: Mapped[str] = mapped_column(String(100))
    input_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupportRun(Base):
    __tablename__ = "support_runs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_support_run_workspace"),
        ForeignKeyConstraint(
            ["workspace_id", "message_id"], ["support_messages.workspace_id", "support_messages.id"]
        ),
        ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
        ForeignKeyConstraint(
            ["workspace_id", "retrieval_id"], ["retrieval_traces.workspace_id", "retrieval_traces.id"]
        ),
        CheckConstraint(
            "state IN ('queued','waiting_for_input','awaiting_review','completed','rejected','cancelled')",
            name="support_run_state",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    message_id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    retrieval_id: Mapped[uuid.UUID | None]
    state: Mapped[str] = mapped_column(String(24), default="queued")
    outcome: Mapped[str | None] = mapped_column(String(32))
    review_kind: Mapped[str] = mapped_column(String(24), default="ordinary")
    review_version: Mapped[int] = mapped_column(default=0)
    reviewed_response: Mapped[str | None] = mapped_column(Text)
    drafted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    draft: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Handoff(Base):
    __tablename__ = "development_handoffs"
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        UniqueConstraint("workspace_id", "run_id", name="uq_handoff_run"),
        UniqueConstraint("workspace_id", "id", name="uq_handoff_workspace"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID]
    context: Mapped[dict] = mapped_column(JSONB)
    context_hash: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(64), default="support-development-v1")
    provider: Mapped[str] = mapped_column(String(40), default="codex_assisted_development")
    response: Mapped[dict | None] = mapped_column(JSONB)
    response_hash: Mapped[str | None] = mapped_column(String(64))
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RunStep(Base):
    __tablename__ = "support_steps"
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    job_attempt: Mapped[int]
    node: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="started")
    duration_ms: Mapped[float | None]
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
