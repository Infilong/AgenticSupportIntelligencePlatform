"""add rendered prompt hash to AI runs

Revision ID: 0025_ai_run_prompt_hash
Revises: 0024_workspace_lifecycle
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0025_ai_run_prompt_hash"
down_revision: str | None = "0024_workspace_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_runs", sa.Column("rendered_prompt_hash", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_runs", "rendered_prompt_hash")
