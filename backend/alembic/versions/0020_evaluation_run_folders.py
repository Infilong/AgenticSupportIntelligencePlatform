"""add evaluation run folders

Revision ID: 0020_evaluation_run_folders
Revises: 0019_graph_trace_span_ids
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020_evaluation_run_folders"
down_revision: str | None = "0019_graph_trace_span_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("folder_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_evaluation_runs_folder_id"), "evaluation_runs", ["folder_id"])
    op.create_foreign_key(
        op.f("fk_evaluation_runs_folder_id_resource_folders"),
        "evaluation_runs",
        "resource_folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_evaluation_runs_folder_id_resource_folders"),
        "evaluation_runs",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_evaluation_runs_folder_id"), table_name="evaluation_runs")
    op.drop_column("evaluation_runs", "folder_id")
