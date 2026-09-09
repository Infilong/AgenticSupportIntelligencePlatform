"""Original messages, processing runs and attributed development handoffs."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007_support"
down_revision = "0006_retrieval"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "support_messages",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original", sa.Text, nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("submission_key", sa.String(100), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workspace_id", "id", name="uq_message_workspace"),
        sa.UniqueConstraint("workspace_id", "submission_key", name="uq_message_submission"),
    )
    op.create_table(
        "support_runs",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("message_id", sa.Uuid, nullable=False),
        sa.Column("job_id", sa.Uuid, nullable=False),
        sa.Column("retrieval_id", sa.Uuid),
        sa.Column("state", sa.String(24), nullable=False),
        sa.Column("draft", sa.Text),
        sa.Column("citations", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("workspace_id", "id", name="uq_support_run_workspace"),
        sa.ForeignKeyConstraint(
            ["workspace_id", "message_id"], ["support_messages.workspace_id", "support_messages.id"]
        ),
        sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
        sa.ForeignKeyConstraint(
            ["workspace_id", "retrieval_id"], ["retrieval_traces.workspace_id", "retrieval_traces.id"]
        ),
        sa.CheckConstraint(
            "state IN ('queued','waiting_development','draft','clarification',"
            "'insufficient_evidence','cancelled')",
            name="support_run_state",
        ),
    )
    op.create_table(
        "development_handoffs",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("run_id", sa.Uuid, nullable=False),
        sa.Column("context", JSONB, nullable=False),
        sa.Column("context_hash", sa.String(64), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("response", JSONB),
        sa.Column("response_hash", sa.String(64)),
        sa.Column("contributor_id", sa.Uuid, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        sa.UniqueConstraint("workspace_id", "run_id", name="uq_handoff_run"),
        sa.UniqueConstraint("workspace_id", "id", name="uq_handoff_workspace"),
    )
    op.create_table(
        "support_steps",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("run_id", sa.Uuid, nullable=False),
        sa.Column("job_id", sa.Uuid, nullable=False),
        sa.Column("job_attempt", sa.Integer, nullable=False),
        sa.Column("node", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("duration_ms", sa.Float),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        sa.ForeignKeyConstraint(["workspace_id", "job_id"], ["jobs.workspace_id", "jobs.id"]),
    )
    for table in ("support_messages", "support_runs", "support_steps"):
        op.create_index(f"ix_{table}_workspace_created", table, ["workspace_id", "created_at"])


def downgrade():
    for table in ("support_steps", "development_handoffs", "support_runs", "support_messages"):
        op.drop_table(table)
