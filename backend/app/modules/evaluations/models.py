import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"
    __table_args__ = (
        UniqueConstraint("workspace_id", "report_sha256", name="uq_evaluation_report"),
        Index("ix_evaluation_workspace_time", "workspace_id", "registered_at", "id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    registered_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    report_sha256: Mapped[str] = mapped_column(String(64))
    source_commit: Mapped[str] = mapped_column(String(40))
    snapshot: Mapped[dict] = mapped_column(JSONB)
