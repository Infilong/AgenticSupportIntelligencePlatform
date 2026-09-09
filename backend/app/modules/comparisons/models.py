"""Persisted comparison identity and distinct, resumable pipeline records."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.modules.support.models import SupportRun  # noqa: F401 - register linked-run FK in fresh workers


class Comparison(Base):
    __tablename__ = "generation_comparisons"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_comparison_workspace"),
        UniqueConstraint("workspace_id", "submission_key", name="uq_comparison_submission"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    submission_key: Mapped[str] = mapped_column(String(100))
    input_hash: Mapped[str] = mapped_column(String(64))
    question: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(2))
    corpus_hash: Mapped[str] = mapped_column(String(64))
    corpus: Mapped[list] = mapped_column(JSONB)
    cancelled: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Pipeline(Base):
    __tablename__ = "generation_pipelines"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "comparison_id"],
            ["generation_comparisons.workspace_id", "generation_comparisons.id"],
        ),
        ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
        ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        ForeignKeyConstraint(
            ["workspace_id", "retrieval_id"], ["retrieval_traces.workspace_id", "retrieval_traces.id"]
        ),
        UniqueConstraint("workspace_id", "comparison_id", "name", name="uq_comparison_pipeline"),
        UniqueConstraint("workspace_id", "run_id", name="uq_pipeline_support_run"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    comparison_id: Mapped[uuid.UUID]
    name: Mapped[str] = mapped_column(String(24))
    configuration: Mapped[dict] = mapped_column(JSONB)
    job_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID | None]
    retrieval_id: Mapped[uuid.UUID | None]
    state: Mapped[str] = mapped_column(String(32), default="queued")
    context: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    request: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    response: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    response_hash: Mapped[str | None] = mapped_column(String(64))
    contributor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
