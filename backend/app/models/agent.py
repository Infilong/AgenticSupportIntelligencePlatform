from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.language import SupportedLanguage
from app.db.base import Base


class GraphRunStatus(StrEnum):
    running = "running"
    completed = "completed"
    needs_human_review = "needs_human_review"
    failed = "failed"


class GraphStepStatus(StrEnum):
    succeeded = "succeeded"
    failed = "failed"


class AgentConfig(Base):
    __tablename__ = "agent_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_config_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("model_configs.id", ondelete="SET NULL"), nullable=True
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resource_folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    token_budget: Mapped[int] = mapped_column(Integer, default=4000, nullable=False)
    settings_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    graph_runs = relationship("GraphRun", back_populates="agent_config")
    folder = relationship("ResourceFolder")


class GraphRun(Base):
    __tablename__ = "graph_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_config_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agent_configs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=True, index=True
    )
    language: Mapped[SupportedLanguage | None] = mapped_column(String(8), nullable=True)
    status: Mapped[GraphRunStatus] = mapped_column(String(40), nullable=False)
    route_decision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    final_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    agent_config = relationship("AgentConfig", back_populates="graph_runs")
    steps = relationship("GraphStep", back_populates="graph_run", cascade="all, delete-orphan")


class GraphStep(Base):
    __tablename__ = "graph_steps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    span_id: Mapped[str | None] = mapped_column(
        String(36), default=lambda: str(uuid.uuid4()), nullable=True, index=True
    )
    parent_span_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GraphStepStatus] = mapped_column(String(40), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_runs.id", ondelete="SET NULL"), nullable=True
    )
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    graph_run = relationship("GraphRun", back_populates="steps")
    tool_calls = relationship("ToolCall", back_populates="graph_step", cascade="all, delete-orphan")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_steps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GraphStepStatus] = mapped_column(String(40), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    graph_step = relationship("GraphStep", back_populates="tool_calls")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checkpoint_key: Mapped[str] = mapped_column(String(160), nullable=False)
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
