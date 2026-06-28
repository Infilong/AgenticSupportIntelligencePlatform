"""add prompt and model archive fields

Revision ID: 0016_prompt_model_archive
Revises: 0015_workspace_budget_policies
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_prompt_model_archive"
down_revision: str | None = "0015_workspace_budget_policies"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "model_configs",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "prompt_templates",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_model_configs_workspace_archived",
        "model_configs",
        ["workspace_id", "archived_at"],
    )
    op.create_index(
        "ix_prompt_templates_workspace_archived",
        "prompt_templates",
        ["workspace_id", "archived_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_prompt_templates_workspace_archived", table_name="prompt_templates")
    op.drop_index("ix_model_configs_workspace_archived", table_name="model_configs")
    op.drop_column("prompt_templates", "archived_at")
    op.drop_column("model_configs", "archived_at")
