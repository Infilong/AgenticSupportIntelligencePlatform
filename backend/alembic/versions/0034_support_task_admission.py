"""Durable task and execution admission, separate from graph execution."""

import sqlalchemy as sa

from alembic import op

revision = "0034_support_task_admission"
down_revision = "0033_admin_operator_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("support_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("agent_config_id", sa.Uuid(),
                  sa.ForeignKey("agent_configs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "request_key", name="uq_task_request_key"))
    op.create_index("ix_support_tasks_workspace_id", "support_tasks", ["workspace_id"])
    op.create_table("task_executions",
        sa.Column("graph_run_id", sa.Uuid(), sa.ForeignKey("graph_runs.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("task_id", sa.Uuid(), sa.ForeignKey("support_tasks.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("initial_state_json", sa.Text(), nullable=False),
        sa.Column("agent_snapshot_json", sa.Text(), nullable=False),
        sa.Column("max_steps", sa.Integer(), nullable=False),
        sa.Column("max_seconds", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("stop_requested_at", sa.DateTime(timezone=True)),
        sa.Column("stopped_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("error_code", sa.String(80)),
        sa.CheckConstraint("max_steps > 0 AND max_seconds > 0", name="ck_task_execution_limits"))
    op.create_index("ix_task_executions_workspace_id", "task_executions", ["workspace_id"])
    op.create_index("ix_task_executions_task_id", "task_executions", ["task_id"])


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE support_tasks, task_executions IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM support_tasks)")):
        raise RuntimeError("Cannot discard persisted support tasks; use forward repair")
    op.drop_table("task_executions")
    op.drop_table("support_tasks")
