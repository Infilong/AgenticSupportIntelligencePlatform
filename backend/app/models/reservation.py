import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelCallReservation(Base):
    __tablename__ = "model_call_reservations"
    __table_args__ = (
        CheckConstraint("(graph_run_id IS NULL) <> (evaluation_run_id IS NULL)",
                        name="ck_reservation_context"),
        CheckConstraint("estimated_tokens >= 0", name="ck_reservation_tokens"),
        CheckConstraint("estimated_cost >= 0", name="ck_reservation_cost"),
        CheckConstraint("status IN ('reserved','consumed','released','denied')",
                        name="ck_reservation_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    graph_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("graph_runs.id", ondelete="CASCADE"), index=True)
    evaluation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    ai_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_runs.id", ondelete="SET NULL"), unique=True)
    purpose: Mapped[str] = mapped_column(String(120))
    estimated_tokens: Mapped[int] = mapped_column(Integer)
    estimated_cost: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20))
    denial_reason: Mapped[str | None] = mapped_column(String(80))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
