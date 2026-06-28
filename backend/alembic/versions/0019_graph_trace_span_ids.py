"""add graph trace and span ids

Revision ID: 0019_graph_trace_span_ids
Revises: 0018_workspace_role_presets
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019_graph_trace_span_ids"
down_revision: str | None = "0018_workspace_role_presets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("graph_runs", sa.Column("trace_id", sa.String(length=36), nullable=True))
    op.add_column("graph_steps", sa.Column("span_id", sa.String(length=36), nullable=True))
    op.add_column("graph_steps", sa.Column("parent_span_id", sa.String(length=36), nullable=True))
    op.create_index("ix_graph_runs_trace_id", "graph_runs", ["trace_id"])
    op.create_index("ix_graph_steps_span_id", "graph_steps", ["span_id"])
    op.create_index("ix_graph_steps_parent_span_id", "graph_steps", ["parent_span_id"])


def downgrade() -> None:
    op.drop_index("ix_graph_steps_parent_span_id", table_name="graph_steps")
    op.drop_index("ix_graph_steps_span_id", table_name="graph_steps")
    op.drop_index("ix_graph_runs_trace_id", table_name="graph_runs")
    op.drop_column("graph_steps", "parent_span_id")
    op.drop_column("graph_steps", "span_id")
    op.drop_column("graph_runs", "trace_id")
