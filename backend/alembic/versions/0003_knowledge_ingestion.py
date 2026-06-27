"""create knowledge ingestion tables

Revision ID: 0003_knowledge_ingestion
Revises: 0002_dataset_curation
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_knowledge_ingestion"
down_revision: str | None = "0002_dataset_curation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class Vector(sa.types.UserDefinedType):
    def get_col_spec(self, **kw) -> str:
        return "vector(16)"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE document_status AS ENUM ('pending', 'indexing', 'indexed', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )
    document_status = postgresql.ENUM(
        "pending",
        "indexing",
        "indexed",
        "failed",
        name="document_status",
        create_type=False,
    )
    supported_language = postgresql.ENUM(
        "en", "ja", "zh", name="supported_language", create_type=False
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("status", document_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_created_by_user_id"),
        "knowledge_documents",
        ["created_by_user_id"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_workspace_id"), "knowledge_documents", ["workspace_id"]
    )

    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_document_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_type", sa.String(length=80), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["knowledge_document_id"], ["knowledge_documents.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "knowledge_document_id",
            "version",
            name="uq_document_version_number",
        ),
    )
    op.create_index(
        op.f("ix_document_versions_knowledge_document_id"),
        "document_versions",
        ["knowledge_document_id"],
    )
    op.create_index(
        op.f("ix_document_versions_workspace_id"), "document_versions", ["workspace_id"]
    )

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("chunk_metadata", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_version_id"], ["document_versions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id",
            "document_version_id",
            "chunk_index",
            name="uq_document_chunk_index",
        ),
    )
    op.create_index(
        op.f("ix_document_chunks_document_version_id"),
        "document_chunks",
        ["document_version_id"],
    )
    op.create_index(op.f("ix_document_chunks_workspace_id"), "document_chunks", ["workspace_id"])

    op.create_table(
        "embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("document_chunk_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("vector", Vector(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_embeddings_document_chunk_id"), "embeddings", ["document_chunk_id"])
    op.create_index(op.f("ix_embeddings_workspace_id"), "embeddings", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_embeddings_workspace_id"), table_name="embeddings")
    op.drop_index(op.f("ix_embeddings_document_chunk_id"), table_name="embeddings")
    op.drop_table("embeddings")
    op.drop_index(op.f("ix_document_chunks_workspace_id"), table_name="document_chunks")
    op.drop_index(op.f("ix_document_chunks_document_version_id"), table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index(op.f("ix_document_versions_workspace_id"), table_name="document_versions")
    op.drop_index(
        op.f("ix_document_versions_knowledge_document_id"), table_name="document_versions"
    )
    op.drop_table("document_versions")
    op.drop_index(op.f("ix_knowledge_documents_workspace_id"), table_name="knowledge_documents")
    op.drop_index(
        op.f("ix_knowledge_documents_created_by_user_id"), table_name="knowledge_documents"
    )
    op.drop_table("knowledge_documents")
    postgresql.ENUM(name="document_status").drop(op.get_bind(), checkfirst=True)
