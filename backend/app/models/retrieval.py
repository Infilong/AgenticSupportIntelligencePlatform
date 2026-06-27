from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.language import SupportedLanguage
from app.db.base import Base


class RetrievalTrace(Base):
    __tablename__ = "retrieval_traces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[SupportedLanguage] = mapped_column(Enum(SupportedLanguage), nullable=False)
    strategy: Mapped[str] = mapped_column(String(40), nullable=False)
    filters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    no_source: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    retrieved_chunks = relationship(
        "RetrievedChunk", back_populates="retrieval_trace", cascade="all, delete-orphan"
    )


class RetrievedChunk(Base):
    __tablename__ = "retrieved_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    retrieval_trace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("retrieval_traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_chunk_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    vector_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lexical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    combined_score: Mapped[float] = mapped_column(Float, nullable=False)
    citation: Mapped[str] = mapped_column(String(500), nullable=False)

    retrieval_trace = relationship("RetrievalTrace", back_populates="retrieved_chunks")
    document_chunk = relationship("DocumentChunk")
