from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkspaceBudgetPolicy(Base):
    __tablename__ = "workspace_budget_policies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    monthly_token_budget: Mapped[int] = mapped_column(Integer, default=100_000, nullable=False)
    monthly_cost_budget: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    per_run_token_budget: Mapped[int] = mapped_column(Integer, default=4_000, nullable=False)
    per_run_cost_budget: Mapped[float] = mapped_column(Float, default=0.05, nullable=False)
    rate_limit_requests_per_hour: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    alert_threshold_percent: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
