"""add evaluation run archive field

Revision ID: 0014_evaluation_run_archive
Revises: 0013_guardrail_policies
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_evaluation_run_archive"
down_revision: str | None = "0013_guardrail_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluation_runs",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_evaluation_runs_workspace_archived",
        "evaluation_runs",
        ["workspace_id", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_evaluation_runs_workspace_archived", table_name="evaluation_runs")
    op.drop_column("evaluation_runs", "archived_at")
