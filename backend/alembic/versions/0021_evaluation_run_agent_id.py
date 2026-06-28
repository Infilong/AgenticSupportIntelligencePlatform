"""add evaluation run agent attribution

Revision ID: 0021_evaluation_run_agent_id
Revises: 0020_evaluation_run_folders
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021_evaluation_run_agent_id"
down_revision: str | None = "0020_evaluation_run_folders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("agent_config_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_evaluation_runs_agent_config_id"), "evaluation_runs", ["agent_config_id"]
    )
    op.create_foreign_key(
        op.f("fk_evaluation_runs_agent_config_id_agent_configs"),
        "evaluation_runs",
        "agent_configs",
        ["agent_config_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_evaluation_runs_agent_config_id_agent_configs"),
        "evaluation_runs",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_evaluation_runs_agent_config_id"), table_name="evaluation_runs")
    op.drop_column("evaluation_runs", "agent_config_id")
