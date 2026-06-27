"""create guardrail and human review tables

Revision ID: 0007_guardrails_human_review
Revises: 0006_agent_workflow
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_guardrails_human_review"
down_revision: str | None = "0006_agent_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guardrail_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=False),
        sa.Column("graph_step_id", sa.Uuid(), nullable=True),
        sa.Column("guardrail_type", sa.String(length=120), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["graph_run_id"], ["graph_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["graph_step_id"], ["graph_steps.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_guardrail_results_graph_run_id"), "guardrail_results", ["graph_run_id"]
    )
    op.create_index(
        op.f("ix_guardrail_results_workspace_id"), "guardrail_results", ["workspace_id"]
    )

    op.create_table(
        "human_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("proposed_answer", sa.Text(), nullable=True),
        sa.Column("reviewer_decision", sa.String(length=40), nullable=False),
        sa.Column("edited_answer", sa.Text(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["graph_run_id"], ["graph_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_human_reviews_graph_run_id"), "human_reviews", ["graph_run_id"])
    op.create_index(op.f("ix_human_reviews_workspace_id"), "human_reviews", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_human_reviews_workspace_id"), table_name="human_reviews")
    op.drop_index(op.f("ix_human_reviews_graph_run_id"), table_name="human_reviews")
    op.drop_table("human_reviews")
    op.drop_index(op.f("ix_guardrail_results_workspace_id"), table_name="guardrail_results")
    op.drop_index(op.f("ix_guardrail_results_graph_run_id"), table_name="guardrail_results")
    op.drop_table("guardrail_results")
