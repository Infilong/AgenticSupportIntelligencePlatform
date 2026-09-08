import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RetrievalTrace(Base):
    __tablename__ = "retrieval_traces"
    __table_args__ = (UniqueConstraint("workspace_id", "id", name="uq_retrieval_workspace"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="started")
    strategy: Mapped[str] = mapped_column(String(64), default="cosine20-lexical20-rrf60-v1")
    results: Mapped[list] = mapped_column(JSONB, default=list)
    duration_ms: Mapped[float | None]
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
