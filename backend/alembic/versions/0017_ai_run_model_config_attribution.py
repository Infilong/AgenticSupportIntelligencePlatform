"""add ai run model config attribution

Revision ID: 0017_ai_run_model_config_attribution
Revises: 0016_prompt_model_archive
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017_ai_run_model_config_attribution"
down_revision: str | None = "0016_prompt_model_archive"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ai_runs",
        sa.Column("model_config_id", sa.Uuid(), nullable=True),
    )
    op.create_index("ix_ai_runs_model_config_id", "ai_runs", ["model_config_id"])
    op.create_foreign_key(
        "fk_ai_runs_model_config_id_model_configs",
        "ai_runs",
        "model_configs",
        ["model_config_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_runs_model_config_id_model_configs", "ai_runs", type_="foreignkey")
    op.drop_index("ix_ai_runs_model_config_id", table_name="ai_runs")
    op.drop_column("ai_runs", "model_config_id")
