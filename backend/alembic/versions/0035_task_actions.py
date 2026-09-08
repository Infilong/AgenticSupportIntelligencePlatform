"""Immutable internal task proposals and deduplicated notes."""

import sqlalchemy as sa

from alembic import op

revision = "0035_task_actions"
down_revision = "0034_support_task_admission"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("task_action_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), sa.ForeignKey("graph_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("support_tasks.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("inputs_json", sa.Text(), nullable=False),
        sa.Column("proposal_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("result_json", sa.Text()),
        sa.Column("reviewer_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT")),
        sa.Column("reason", sa.String(2000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("graph_run_id", "proposal_hash", name="uq_task_action_proposal"),
        sa.CheckConstraint("status IN ('pending','applied','rejected')",
                           name="ck_task_action_status"))
    for column in ("workspace_id", "graph_run_id"):
        op.create_index(f"ix_task_action_proposals_{column}", "task_action_proposals", [column])
    op.create_table("task_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("support_tasks.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("proposal_id", sa.Uuid(),
                  sa.ForeignKey("task_action_proposals.id", ondelete="RESTRICT"),
                  nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for column in ("workspace_id", "task_id"):
        op.create_index(f"ix_task_notes_{column}", "task_notes", [column])


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE task_action_proposals, task_notes IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM task_action_proposals)")):
        raise RuntimeError("Cannot discard task action history; use forward repair")
    op.drop_table("task_notes")
    op.drop_table("task_action_proposals")
