"""Retain workspace-scoped retrieval traces independently of answer generation."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0006_retrieval"
down_revision = "0005_model_calls"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "retrieval_traces",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("strategy", sa.String(64), nullable=False),
        sa.Column("results", JSONB, nullable=False),
        sa.Column("duration_ms", sa.Float),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "id", name="uq_retrieval_workspace"),
    )
    op.create_index("ix_retrieval_workspace_created", "retrieval_traces", ["workspace_id", "created_at"])
    op.add_column("model_calls", sa.Column("retrieval_id", sa.Uuid))
    op.create_foreign_key(
        "fk_model_call_retrieval",
        "model_calls",
        "retrieval_traces",
        ["workspace_id", "retrieval_id"],
        ["workspace_id", "id"],
    )


def downgrade():
    op.drop_constraint("fk_model_call_retrieval", "model_calls", type_="foreignkey")
    op.drop_column("model_calls", "retrieval_id")
    op.drop_table("retrieval_traces")
