from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.language import SupportedLanguage
from app.db.base import Base


class ImportSourceType(StrEnum):
    jsonl = "jsonl"
    csv = "csv"


class ImportStatus(StrEnum):
    completed = "completed"
    failed = "failed"


class ExampleStatus(StrEnum):
    imported = "imported"
    active = "active"


class MessageRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"


class LabelSource(StrEnum):
    import_ = "import"
    human = "human"


class LabelType(StrEnum):
    intent = "intent"
    sentiment = "sentiment"
    product_area = "product_area"
    escalation_needed = "escalation_needed"
    safety_risk = "safety_risk"
    response_quality = "response_quality"


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("resource_folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    workspace = relationship("Workspace")
    folder = relationship("ResourceFolder")
    import_batches = relationship(
        "ImportBatch", back_populates="dataset", cascade="all, delete-orphan"
    )
    examples = relationship(
        "ConversationExample", back_populates="dataset", cascade="all, delete-orphan"
    )


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[ImportSourceType] = mapped_column(Enum(ImportSourceType), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(Enum(ImportStatus), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    dataset = relationship("Dataset", back_populates="import_batches")
    examples = relationship("ConversationExample", back_populates="import_batch")


class ConversationExample(Base):
    __tablename__ = "conversation_examples"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    language: Mapped[SupportedLanguage] = mapped_column(Enum(SupportedLanguage), nullable=False)
    status: Mapped[ExampleStatus] = mapped_column(Enum(ExampleStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    dataset = relationship("Dataset", back_populates="examples")
    import_batch = relationship("ImportBatch", back_populates="examples")
    messages = relationship(
        "Message", back_populates="conversation_example", cascade="all, delete-orphan"
    )
    labels = relationship(
        "Label", back_populates="conversation_example", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_example_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversation_examples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    language: Mapped[SupportedLanguage] = mapped_column(Enum(SupportedLanguage), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    conversation_example = relationship("ConversationExample", back_populates="messages")


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "conversation_example_id",
            "label_type",
            "source",
            name="uq_label_example_type_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_example_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("conversation_examples.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label_type: Mapped[LabelType] = mapped_column(Enum(LabelType), nullable=False)
    value: Mapped[str] = mapped_column(String(240), nullable=False)
    source: Mapped[LabelSource] = mapped_column(
        Enum(LabelSource, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    conversation_example = relationship("ConversationExample", back_populates="labels")
    created_by_user = relationship("User")
