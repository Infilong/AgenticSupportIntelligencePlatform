"""add workspace lifecycle fields

Revision ID: 0024_workspace_lifecycle
Revises: 0023_eval_result_graph_run
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0024_workspace_lifecycle"
down_revision: str | None = "0023_eval_result_graph_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workspaces", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workspaces", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_workspaces_archived_at"), "workspaces", ["archived_at"])
    op.create_index(op.f("ix_workspaces_deleted_at"), "workspaces", ["deleted_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_workspaces_deleted_at"), table_name="workspaces")
    op.drop_index(op.f("ix_workspaces_archived_at"), table_name="workspaces")
    op.drop_column("workspaces", "deleted_at")
    op.drop_column("workspaces", "archived_at")
