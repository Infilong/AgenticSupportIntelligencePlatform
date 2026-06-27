"""create agent workflow tables

Revision ID: 0006_agent_workflow
Revises: 0005_ai_observability
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_agent_workflow"
down_revision: str | None = "0005_ai_observability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("model_config_id", sa.Uuid(), nullable=True),
        sa.Column("token_budget", sa.Integer(), nullable=False),
        sa.Column("settings_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_config_id"], ["model_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_configs_workspace_id"), "agent_configs", ["workspace_id"])

    op.create_table(
        "graph_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("agent_config_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("route_decision", sa.String(length=80), nullable=True),
        sa.Column("final_answer", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_config_id"], ["agent_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graph_runs_agent_config_id"), "graph_runs", ["agent_config_id"])
    op.create_index(op.f("ix_graph_runs_user_id"), "graph_runs", ["user_id"])
    op.create_index(op.f("ix_graph_runs_workspace_id"), "graph_runs", ["workspace_id"])

    op.create_table(
        "graph_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=False),
        sa.Column("step_name", sa.String(length=120), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("ai_run_id", sa.Uuid(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["ai_run_id"], ["ai_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["graph_run_id"], ["graph_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_graph_steps_graph_run_id"), "graph_steps", ["graph_run_id"])
    op.create_index(op.f("ix_graph_steps_workspace_id"), "graph_steps", ["workspace_id"])

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=False),
        sa.Column("graph_step_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("input_json", sa.Text(), nullable=False),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["graph_run_id"], ["graph_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["graph_step_id"], ["graph_steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_calls_graph_run_id"), "tool_calls", ["graph_run_id"])
    op.create_index(op.f("ix_tool_calls_graph_step_id"), "tool_calls", ["graph_step_id"])
    op.create_index(op.f("ix_tool_calls_workspace_id"), "tool_calls", ["workspace_id"])

    op.create_table(
        "checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_key", sa.String(length=160), nullable=False),
        sa.Column("state_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["graph_run_id"], ["graph_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_checkpoints_graph_run_id"), "checkpoints", ["graph_run_id"])
    op.create_index(op.f("ix_checkpoints_workspace_id"), "checkpoints", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_checkpoints_workspace_id"), table_name="checkpoints")
    op.drop_index(op.f("ix_checkpoints_graph_run_id"), table_name="checkpoints")
    op.drop_table("checkpoints")
    op.drop_index(op.f("ix_tool_calls_workspace_id"), table_name="tool_calls")
    op.drop_index(op.f("ix_tool_calls_graph_step_id"), table_name="tool_calls")
    op.drop_index(op.f("ix_tool_calls_graph_run_id"), table_name="tool_calls")
    op.drop_table("tool_calls")
    op.drop_index(op.f("ix_graph_steps_workspace_id"), table_name="graph_steps")
    op.drop_index(op.f("ix_graph_steps_graph_run_id"), table_name="graph_steps")
    op.drop_table("graph_steps")
    op.drop_index(op.f("ix_graph_runs_workspace_id"), table_name="graph_runs")
    op.drop_index(op.f("ix_graph_runs_user_id"), table_name="graph_runs")
    op.drop_index(op.f("ix_graph_runs_agent_config_id"), table_name="graph_runs")
    op.drop_table("graph_runs")
    op.drop_index(op.f("ix_agent_configs_workspace_id"), table_name="agent_configs")
    op.drop_table("agent_configs")
