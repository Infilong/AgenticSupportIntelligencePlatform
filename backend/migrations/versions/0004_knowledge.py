"""Versioned originals and authorized published document vectors."""

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0004_knowledge"
down_revision = "0003_jobs"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("uq_job_workspace", "jobs", ["workspace_id", "id"])
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("withdrawn", sa.Boolean, nullable=False),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("active_version_id", sa.Uuid),
        sa.Column("desired_version_id", sa.Uuid),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "id", name="uq_document_workspace"),
    )
    op.create_table(
        "document_versions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("document_id", sa.Uuid, nullable=False),
        sa.Column("job_id", sa.Uuid, nullable=False),
        sa.Column("number", sa.Integer, nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("original", sa.LargeBinary, nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "id", name="uq_version_workspace"),
        sa.UniqueConstraint("workspace_id", "document_id", "id", name="uq_version_document"),
        sa.UniqueConstraint("workspace_id", "document_id", "number", name="uq_version_number"),
        sa.ForeignKeyConstraint(["workspace_id", "document_id"], ["documents.workspace_id", "documents.id"]),
        sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
    )
    for field in ("active", "desired"):
        op.create_foreign_key(
            f"fk_document_{field}_version",
            "documents",
            "document_versions",
            ["workspace_id", "id", f"{field}_version_id"],
            ["workspace_id", "document_id", "id"],
        )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("version_id", sa.Uuid, nullable=False),
        sa.Column("ordinal", sa.Integer, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("start_offset", sa.Integer, nullable=False),
        sa.Column("end_offset", sa.Integer, nullable=False),
        sa.Column("section", sa.String(200), nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("embedding_space", sa.String(160), nullable=False),
        sa.Column("lexical_terms", sa.ARRAY(sa.Text), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id", "version_id"], ["document_versions.workspace_id", "document_versions.id"]
        ),
        sa.UniqueConstraint("workspace_id", "version_id", "ordinal", name="uq_chunk_ordinal"),
    )
    op.create_index("ix_chunks_workspace", "document_chunks", ["workspace_id", "version_id"])


def downgrade():
    op.drop_table("document_chunks")
    for field in ("active", "desired"):
        op.drop_constraint(f"fk_document_{field}_version", "documents", type_="foreignkey")
    op.drop_table("document_versions")
    op.drop_table("documents")
    op.drop_constraint("uq_job_workspace", "jobs", type_="unique")
