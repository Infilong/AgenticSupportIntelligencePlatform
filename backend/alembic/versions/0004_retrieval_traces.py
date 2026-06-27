"""create retrieval trace tables

Revision ID: 0004_retrieval_traces
Revises: 0003_knowledge_ingestion
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_retrieval_traces"
down_revision: str | None = "0003_knowledge_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    supported_language = postgresql.ENUM(
        "en", "ja", "zh", name="supported_language", create_type=False
    )
    op.create_table(
        "retrieval_traces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("strategy", sa.String(length=40), nullable=False),
        sa.Column("filters_json", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("no_source", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_retrieval_traces_graph_run_id"), "retrieval_traces", ["graph_run_id"])
    op.create_index(op.f("ix_retrieval_traces_workspace_id"), "retrieval_traces", ["workspace_id"])

    op.create_table(
        "retrieved_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("retrieval_trace_id", sa.Uuid(), nullable=False),
        sa.Column("document_chunk_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("vector_score", sa.Float(), nullable=True),
        sa.Column("lexical_score", sa.Float(), nullable=True),
        sa.Column("combined_score", sa.Float(), nullable=False),
        sa.Column("citation", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["document_chunk_id"], ["document_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["retrieval_trace_id"], ["retrieval_traces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_retrieved_chunks_document_chunk_id"),
        "retrieved_chunks",
        ["document_chunk_id"],
    )
    op.create_index(
        op.f("ix_retrieved_chunks_retrieval_trace_id"),
        "retrieved_chunks",
        ["retrieval_trace_id"],
    )
    op.create_index(op.f("ix_retrieved_chunks_workspace_id"), "retrieved_chunks", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_retrieved_chunks_workspace_id"), table_name="retrieved_chunks")
    op.drop_index(op.f("ix_retrieved_chunks_retrieval_trace_id"), table_name="retrieved_chunks")
    op.drop_index(op.f("ix_retrieved_chunks_document_chunk_id"), table_name="retrieved_chunks")
    op.drop_table("retrieved_chunks")
    op.drop_index(op.f("ix_retrieval_traces_workspace_id"), table_name="retrieval_traces")
    op.drop_index(op.f("ix_retrieval_traces_graph_run_id"), table_name="retrieval_traces")
    op.drop_table("retrieval_traces")
