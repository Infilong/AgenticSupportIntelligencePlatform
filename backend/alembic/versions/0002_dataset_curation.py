"""create dataset curation tables

Revision ID: 0002_dataset_curation
Revises: 0001_auth_workspace
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_dataset_curation"
down_revision: str | None = "0001_auth_workspace"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    import_source_type = sa.Enum("jsonl", "csv", name="import_source_type")
    import_status = sa.Enum("completed", "failed", name="import_status")
    supported_language = sa.Enum("en", "ja", "zh", name="supported_language")
    example_status = sa.Enum("imported", "active", name="example_status")
    message_role = sa.Enum("user", "assistant", "system", name="message_role")
    label_type = sa.Enum(
        "intent",
        "sentiment",
        "product_area",
        "escalation_needed",
        "safety_risk",
        "response_quality",
        name="label_type",
    )
    label_source = sa.Enum("import", "human", name="label_source")

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_datasets_workspace_id"), "datasets", ["workspace_id"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("source_type", import_source_type, nullable=False),
        sa.Column("status", import_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_batches_dataset_id"), "import_batches", ["dataset_id"])
    op.create_index(op.f("ix_import_batches_workspace_id"), "import_batches", ["workspace_id"])

    op.create_table(
        "conversation_examples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=160), nullable=True),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("status", example_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["import_batch_id"], ["import_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_conversation_examples_dataset_id"), "conversation_examples", ["dataset_id"]
    )
    op.create_index(
        op.f("ix_conversation_examples_import_batch_id"),
        "conversation_examples",
        ["import_batch_id"],
    )
    op.create_index(
        op.f("ix_conversation_examples_workspace_id"), "conversation_examples", ["workspace_id"]
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_example_id", sa.Uuid(), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_example_id"], ["conversation_examples.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_messages_conversation_example_id"), "messages", ["conversation_example_id"]
    )
    op.create_index(op.f("ix_messages_workspace_id"), "messages", ["workspace_id"])

    op.create_table(
        "labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_example_id", sa.Uuid(), nullable=False),
        sa.Column("label_type", label_type, nullable=False),
        sa.Column("value", sa.String(length=240), nullable=False),
        sa.Column("source", label_source, nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_example_id"], ["conversation_examples.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "conversation_example_id",
            "label_type",
            "source",
            name="uq_label_example_type_source",
        ),
    )
    op.create_index(
        op.f("ix_labels_conversation_example_id"), "labels", ["conversation_example_id"]
    )
    op.create_index(op.f("ix_labels_workspace_id"), "labels", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_labels_workspace_id"), table_name="labels")
    op.drop_index(op.f("ix_labels_conversation_example_id"), table_name="labels")
    op.drop_table("labels")
    op.drop_index(op.f("ix_messages_workspace_id"), table_name="messages")
    op.drop_index(op.f("ix_messages_conversation_example_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(
        op.f("ix_conversation_examples_workspace_id"), table_name="conversation_examples"
    )
    op.drop_index(
        op.f("ix_conversation_examples_import_batch_id"), table_name="conversation_examples"
    )
    op.drop_index(
        op.f("ix_conversation_examples_dataset_id"), table_name="conversation_examples"
    )
    op.drop_table("conversation_examples")
    op.drop_index(op.f("ix_import_batches_workspace_id"), table_name="import_batches")
    op.drop_index(op.f("ix_import_batches_dataset_id"), table_name="import_batches")
    op.drop_table("import_batches")
    op.drop_index(op.f("ix_datasets_workspace_id"), table_name="datasets")
    op.drop_table("datasets")
    for enum_name in [
        "label_source",
        "label_type",
        "message_role",
        "example_status",
        "supported_language",
        "import_status",
        "import_source_type",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
