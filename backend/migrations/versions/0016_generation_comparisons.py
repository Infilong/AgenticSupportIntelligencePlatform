"""Workspace-scoped resumable four-pipeline comparisons."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016_generation_comparisons"
down_revision = "0015_generation_request"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "generation_comparisons",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("workspace_id", sa.UUID(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("submission_key", sa.String(100), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("corpus_hash", sa.String(64), nullable=False),
        sa.Column("corpus", JSONB(), nullable=False),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "id", name="uq_comparison_workspace"),
        sa.UniqueConstraint("workspace_id", "submission_key", name="uq_comparison_submission"),
    )
    op.create_table(
        "generation_pipelines",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("comparison_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(24), nullable=False),
        sa.Column("configuration", JSONB(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID()),
        sa.Column("retrieval_id", sa.UUID()),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("context", JSONB()),
        sa.Column("request", JSONB()),
        sa.Column("request_hash", sa.String(64)),
        sa.Column("response", JSONB()),
        sa.Column("response_hash", sa.String(64)),
        sa.Column("contributor_id", sa.UUID(), sa.ForeignKey("users.id")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(
            ["workspace_id", "comparison_id"],
            ["generation_comparisons.workspace_id", "generation_comparisons.id"],
        ),
        sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
        sa.ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        sa.ForeignKeyConstraint(
            ["workspace_id", "retrieval_id"], ["retrieval_traces.workspace_id", "retrieval_traces.id"]
        ),
        sa.UniqueConstraint("workspace_id", "comparison_id", "name", name="uq_comparison_pipeline"),
        sa.UniqueConstraint("workspace_id", "run_id", name="uq_pipeline_support_run"),
    )


def downgrade():
    op.drop_table("generation_pipelines")
    op.drop_table("generation_comparisons")
