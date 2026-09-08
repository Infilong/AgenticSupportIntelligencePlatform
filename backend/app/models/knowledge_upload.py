"""Durable ingestion job; original bytes are loaded only for extraction/download."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KnowledgeUpload(Base):
    __tablename__ = "knowledge_uploads"
    __table_args__ = (
        UniqueConstraint("workspace_id", "request_key", name="uq_knowledge_upload_request"),
        CheckConstraint("length(original_bytes) BETWEEN 1 AND 20971520",
                        name="ck_knowledge_upload_size"),
        CheckConstraint("attempt_count >= 0", name="ck_knowledge_upload_attempts"),
        CheckConstraint("state IN ('uploaded','extracting','chunking','embedding',"
                        "'ready','failed','requires_ocr')", name="ck_knowledge_upload_state"),
        CheckConstraint("state != 'ready' OR (document_version_id IS NOT NULL "
                        "AND extracted_text IS NOT NULL AND length(extracted_text) > 0)",
                        name="ck_knowledge_upload_ready"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(Uuid,
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(Uuid,
        ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=True)
    request_key: Mapped[str] = mapped_column(String(100), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    filename: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False)
    original_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False, deferred=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded", index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lease_token: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True, deferred=True)
    extraction_metadata: Mapped[str | None] = mapped_column(Text, nullable=True, deferred=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
        nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
