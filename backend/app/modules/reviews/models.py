import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, ForeignKeyConstraint, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    __table_args__ = (
        ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        UniqueConstraint("workspace_id", "run_id", name="uq_review_run"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    run_id: Mapped[uuid.UUID]
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    revision: Mapped[int]
    draft_hash: Mapped[str] = mapped_column(String(64))
    payload_hash: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
