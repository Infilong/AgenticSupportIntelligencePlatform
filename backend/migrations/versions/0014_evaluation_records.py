"""Immutable, workspace-bound historical evaluation projections."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_evaluation_records"
down_revision = "0013_workspace_defaults"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evaluation_records",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("workspace_id", sa.UUID(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("registered_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("report_sha256", sa.String(64), nullable=False),
        sa.Column("source_commit", sa.String(40), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("workspace_id", "report_sha256", name="uq_evaluation_report"),
    )
    op.create_index(
        "ix_evaluation_workspace_time", "evaluation_records", ["workspace_id", "registered_at", "id"]
    )


def downgrade():
    op.drop_table("evaluation_records")
