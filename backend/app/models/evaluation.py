from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.language import SupportedLanguage
from app.db.base import Base


class EvaluationRunStatus(StrEnum):
    running = "running"
    completed = "completed"
    failed = "failed"


class EvaluationMode(StrEnum):
    direct_llm = "direct_llm"
    vector_rag = "vector_rag"
    system_v1 = "system_v1"


class EvaluationCase(Base):
    __tablename__ = "evaluation_cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    language: Mapped[SupportedLanguage] = mapped_column(String(8), nullable=False, index=True)
    input_message: Mapped[str] = mapped_column(Text, nullable=False)
    expected_intent: Mapped[str | None] = mapped_column(String(120), nullable=True)
    expected_sources_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    must_include_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    must_not_include_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    expected_route: Mapped[str] = mapped_column(String(80), nullable=False)
    safety_risk: Mapped[str] = mapped_column(String(40), nullable=False)
    max_prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    modes_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[EvaluationRunStatus] = mapped_column(String(40), nullable=False)
    total_cases: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results = relationship("EvaluationResult", back_populates="evaluation_run")
    metrics = relationship("EvaluationMetric", back_populates="evaluation_run")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluation_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[EvaluationMode] = mapped_column(String(40), nullable=False, index=True)
    language: Mapped[SupportedLanguage] = mapped_column(String(8), nullable=False, index=True)
    actual_route: Mapped[str] = mapped_column(String(80), nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    scores_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Float, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    evaluation_run = relationship("EvaluationRun", back_populates="results")


class EvaluationMetric(Base):
    __tablename__ = "evaluation_metrics"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evaluation_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[EvaluationMode] = mapped_column(String(40), nullable=False, index=True)
    language: Mapped[SupportedLanguage] = mapped_column(String(8), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    evaluation_run = relationship("EvaluationRun", back_populates="metrics")
