"""add workspace guardrail policies

Revision ID: 0013_guardrail_policies
Revises: 0012_tool_configs
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_guardrail_policies"
down_revision: str | None = "0012_tool_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guardrail_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("guardrail_type", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("action_on_fail", sa.String(length=80), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", "guardrail_type", name="uq_guardrail_policy_workspace_type"
        ),
    )
    op.create_index(
        op.f("ix_guardrail_policies_workspace_id"), "guardrail_policies", ["workspace_id"]
    )
    op.create_index(
        op.f("ix_guardrail_policies_guardrail_type"), "guardrail_policies", ["guardrail_type"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_guardrail_policies_guardrail_type"), table_name="guardrail_policies")
    op.drop_index(op.f("ix_guardrail_policies_workspace_id"), table_name="guardrail_policies")
    op.drop_table("guardrail_policies")
