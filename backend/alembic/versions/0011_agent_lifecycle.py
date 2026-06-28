"""add agent lifecycle archive field

Revision ID: 0011_agent_lifecycle
Revises: 0010_resource_folders
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0011_agent_lifecycle"
down_revision: str | None = "0010_resource_folders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent_configs",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_configs_workspace_archived",
        "agent_configs",
        ["workspace_id", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_configs_workspace_archived", table_name="agent_configs")
    op.drop_column("agent_configs", "archived_at")
