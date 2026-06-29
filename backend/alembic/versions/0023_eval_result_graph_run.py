"""link evaluation results to graph runs

Revision ID: 0023_eval_result_graph_run
Revises: 0022_agent_config_folders
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0023_eval_result_graph_run"
down_revision: str | None = "0022_agent_config_folders"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluation_results", sa.Column("graph_run_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_evaluation_results_graph_run_id"), "evaluation_results", ["graph_run_id"]
    )
    op.create_foreign_key(
        op.f("fk_evaluation_results_graph_run_id_graph_runs"),
        "evaluation_results",
        "graph_runs",
        ["graph_run_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_evaluation_results_graph_run_id_graph_runs"),
        "evaluation_results",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_evaluation_results_graph_run_id"), table_name="evaluation_results")
    op.drop_column("evaluation_results", "graph_run_id")
