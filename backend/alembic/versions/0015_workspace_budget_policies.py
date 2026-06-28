"""add workspace budget policies

Revision ID: 0015_workspace_budget_policies
Revises: 0014_evaluation_run_archive
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_workspace_budget_policies"
down_revision: str | None = "0014_evaluation_run_archive"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_budget_policies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("monthly_token_budget", sa.Integer(), nullable=False),
        sa.Column("monthly_cost_budget", sa.Float(), nullable=False),
        sa.Column("per_run_token_budget", sa.Integer(), nullable=False),
        sa.Column("per_run_cost_budget", sa.Float(), nullable=False),
        sa.Column("rate_limit_requests_per_hour", sa.Integer(), nullable=False),
        sa.Column("alert_threshold_percent", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id"),
    )
    op.create_index(
        op.f("ix_workspace_budget_policies_workspace_id"),
        "workspace_budget_policies",
        ["workspace_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_workspace_budget_policies_workspace_id"),
        table_name="workspace_budget_policies",
    )
    op.drop_table("workspace_budget_policies")
