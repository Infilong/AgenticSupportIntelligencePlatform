"""Record actual local embedding attempts without claiming provider billing."""

import sqlalchemy as sa
from alembic import op

revision = "0005_model_calls"
down_revision = "0004_knowledge"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_calls",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", sa.Uuid),
        sa.Column("job_attempt", sa.Integer),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("revision", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("input_tokens", sa.Integer),
        sa.Column("duration_ms", sa.Float),
        sa.Column("api_cost_usd", sa.Float),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
    )
    op.create_index("ix_model_calls_workspace_job", "model_calls", ["workspace_id", "job_id"])


def downgrade():
    op.drop_table("model_calls")
