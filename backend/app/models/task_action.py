"""Immutable proposed inputs and an atomic, deduplicated task update outcome."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskActionProposal(Base):
    __tablename__ = "task_action_proposals"
    __table_args__ = (
        UniqueConstraint("graph_run_id", "proposal_hash", name="uq_task_action_proposal"),
        CheckConstraint("status IN ('pending','applied','rejected')", name="ck_task_action_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("support_tasks.id", ondelete="CASCADE"), nullable=False)
    inputs_json: Mapped[str] = mapped_column(Text, nullable=False)
    proposal_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_json: Mapped[str | None] = mapped_column(Text)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"))
    reason: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               default=lambda: datetime.now(UTC), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TaskNote(Base):
    __tablename__ = "task_notes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("support_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("task_action_proposals.id", ondelete="RESTRICT"), nullable=False,
        unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               default=lambda: datetime.now(UTC), nullable=False)
