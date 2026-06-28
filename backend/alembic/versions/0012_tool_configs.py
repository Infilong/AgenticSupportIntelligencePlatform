"""add workspace tool configs

Revision ID: 0012_tool_configs
Revises: 0011_agent_lifecycle
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_tool_configs"
down_revision: str | None = "0011_agent_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("tool_name", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("timeout_ms", sa.Integer(), nullable=True),
        sa.Column("max_retries", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "tool_name", name="uq_tool_config_workspace_tool"),
    )
    op.create_index(op.f("ix_tool_configs_workspace_id"), "tool_configs", ["workspace_id"])
    op.create_index(op.f("ix_tool_configs_tool_name"), "tool_configs", ["tool_name"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tool_configs_tool_name"), table_name="tool_configs")
    op.drop_index(op.f("ix_tool_configs_workspace_id"), table_name="tool_configs")
    op.drop_table("tool_configs")
