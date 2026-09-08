"""Linked retry metadata; existing admission rows remain unchanged."""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskAttempt(Base):
    __tablename__ = "task_attempts"
    __table_args__ = (UniqueConstraint("workspace_id", "request_key",
                                     name="uq_task_attempt_request_key"),)
    graph_run_id: Mapped[uuid.UUID] = mapped_column(Uuid,
        ForeignKey("graph_runs.id", ondelete="CASCADE"), primary_key=True)
    clarification_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_run_id: Mapped[uuid.UUID] = mapped_column(Uuid,
        ForeignKey("graph_runs.id", ondelete="RESTRICT"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    request_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    corrected_instructions: Mapped[str] = mapped_column(Text, nullable=False)
