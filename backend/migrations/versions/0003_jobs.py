"""PostgreSQL scheduling with bounded retries and fenced leases."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003_jobs"
down_revision = "0002_identity"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("attempts", sa.Integer, nullable=False),
        sa.Column("max_attempts", sa.Integer, nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("lease_token", sa.Uuid),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("cancel_requested", sa.Boolean, nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("result", JSONB),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("workspace_id", "idempotency_key", name="uq_job_key"),
        sa.CheckConstraint(
            "state IN ('queued','running','succeeded','failed','cancelled')", name="job_state"
        ),
        sa.CheckConstraint("attempts >= 0 AND max_attempts BETWEEN 1 AND 5", name="job_attempts"),
    )
    op.create_index("ix_jobs_schedule", "jobs", ["state", "available_at", "priority"])


def downgrade():
    op.drop_table("jobs")
