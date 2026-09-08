import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_document_workspace"),
        ForeignKeyConstraint(
            ["workspace_id", "id", "active_version_id"],
            ["document_versions.workspace_id", "document_versions.document_id", "document_versions.id"],
            name="fk_document_active_version",
            use_alter=True,
        ),
        ForeignKeyConstraint(
            ["workspace_id", "id", "desired_version_id"],
            ["document_versions.workspace_id", "document_versions.document_id", "document_versions.id"],
            name="fk_document_desired_version",
            use_alter=True,
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    title: Mapped[str] = mapped_column(String(200))
    withdrawn: Mapped[bool] = mapped_column(default=False)
    version_number: Mapped[int] = mapped_column(default=0)
    active_version_id: Mapped[uuid.UUID | None]
    desired_version_id: Mapped[uuid.UUID | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("workspace_id", "id", name="uq_version_workspace"),
        UniqueConstraint("workspace_id", "document_id", "id", name="uq_version_document"),
        UniqueConstraint("workspace_id", "document_id", "number", name="uq_version_number"),
        ForeignKeyConstraint(["workspace_id", "document_id"], ["documents.workspace_id", "documents.id"]),
        ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    document_id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    number: Mapped[int]
    filename: Mapped[str] = mapped_column(String(200))
    original: Mapped[bytes] = mapped_column(LargeBinary)
    checksum: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Chunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["document_versions.workspace_id", "document_versions.id"]
        ),
        UniqueConstraint("workspace_id", "version_id", "ordinal", name="uq_chunk_ordinal"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID]
    version_id: Mapped[uuid.UUID]
    ordinal: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    start_offset: Mapped[int]
    end_offset: Mapped[int]
    section: Mapped[str] = mapped_column(String(200))
    token_count: Mapped[int]
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    embedding_space: Mapped[str] = mapped_column(String(160))
    lexical_terms: Mapped[list[str]] = mapped_column(ARRAY(Text))
