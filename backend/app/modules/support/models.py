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
from app.modules.conversations.models import MessageImport  # noqa: F401


class Message(Base):
    __tablename__ = "support_messages"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_message_workspace"),
        UniqueConstraint("workspace_id", "submission_key", name="uq_message_submission"),
        ForeignKeyConstraint(
            ["workspace_id", "import_id"], ["message_imports.workspace_id", "message_imports.id"]
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    original: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    submission_key: Mapped[str] = mapped_column(String(100))
    input_hash: Mapped[str] = mapped_column(String(64))
    labels: Mapped[list] = mapped_column(JSONB, default=list, server_default="[]")
    import_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SupportRun(Base):
    __tablename__ = "support_runs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_support_run_workspace"),
        UniqueConstraint("workspace_id", "message_id", "id", name="uq_run_message"),
        UniqueConstraint("workspace_id", "message_id", "attempt_number", name="uq_run_attempt"),
        UniqueConstraint("workspace_id", "submission_key", name="uq_run_submission"),
        CheckConstraint("attempt_number BETWEEN 1 AND 10", name="run_attempt_number"),
        CheckConstraint("char_length(input_text) BETWEEN 1 AND 1000", name="run_input_size"),
        CheckConstraint(
            "(attempt_kind='initial' AND parent_run_id IS NULL AND attempt_number=1) OR "
            "(attempt_kind IN ('retry','clarify') AND parent_run_id IS NOT NULL AND attempt_number>1)",
            name="run_attempt_kind",
        ),
        ForeignKeyConstraint(
            ["workspace_id", "message_id", "parent_run_id"],
            ["support_runs.workspace_id", "support_runs.message_id", "support_runs.id"],
            name="fk_run_parent",
        ),
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
    parent_run_id: Mapped[uuid.UUID | None]
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    attempt_number: Mapped[int] = mapped_column(default=1)
    attempt_kind: Mapped[str] = mapped_column(String(16), default="initial")
    input_text: Mapped[str] = mapped_column(Text)
    clarification: Mapped[str | None] = mapped_column(Text)
    submission_key: Mapped[str | None] = mapped_column(String(100))
    submission_hash: Mapped[str | None] = mapped_column(String(64))
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
        CheckConstraint(
            "(generation_request IS NULL) = (request_hash IS NULL)", name="handoff_request_pair"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID]
    context: Mapped[dict] = mapped_column(JSONB)
    context_hash: Mapped[str] = mapped_column(String(64))
    generation_request: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    request_hash: Mapped[str | None] = mapped_column(String(64))
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
