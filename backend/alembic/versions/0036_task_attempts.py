"""Preserve linked retry provenance without rewriting existing task history."""

import sqlalchemy as sa

from alembic import op

revision = "0036_task_attempts"
down_revision = "0035_task_actions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("task_attempts",
        sa.Column("graph_run_id", sa.Uuid(), sa.ForeignKey("graph_runs.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("parent_run_id", sa.Uuid(), sa.ForeignKey("graph_runs.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("corrected_instructions", sa.Text(), nullable=False),
        sa.UniqueConstraint("workspace_id", "request_key", name="uq_task_attempt_request_key"))
    op.create_index("ix_task_attempts_workspace_id", "task_attempts", ["workspace_id"])


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE task_attempts IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM task_attempts)")):
        raise RuntimeError("Cannot discard linked task attempt history; use forward repair")
    op.drop_table("task_attempts")
