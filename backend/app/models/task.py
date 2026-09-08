"""Durable support tasks and execution admission records."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SupportTask(Base):
    __tablename__ = "support_tasks"
    __table_args__ = (UniqueConstraint("workspace_id", "request_key", name="uq_task_request_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    agent_config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agent_configs.id", ondelete="RESTRICT"), nullable=False)
    request_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    input_envelope_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               default=lambda: datetime.now(UTC), nullable=False)


class TaskExecution(Base):
    __tablename__ = "task_executions"
    __table_args__ = (
        CheckConstraint("max_steps > 0 AND max_seconds > 0", name="ck_task_execution_limits"),
    )

    graph_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), primary_key=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("support_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    initial_state_json: Mapped[str] = mapped_column(Text, nullable=False)
    agent_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    max_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    max_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stop_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    stopped_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
