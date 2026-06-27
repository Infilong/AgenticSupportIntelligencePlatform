"""create evaluation tables

Revision ID: 0008_evaluation
Revises: 0007_guardrails_human_review
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_evaluation"
down_revision: str | None = "0007_guardrails_human_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluation_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("input_message", sa.Text(), nullable=False),
        sa.Column("expected_intent", sa.String(length=120), nullable=True),
        sa.Column("expected_sources_json", sa.Text(), nullable=False),
        sa.Column("must_include_json", sa.Text(), nullable=False),
        sa.Column("must_not_include_json", sa.Text(), nullable=False),
        sa.Column("expected_route", sa.String(length=80), nullable=False),
        sa.Column("safety_risk", sa.String(length=40), nullable=False),
        sa.Column("max_prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_cases_external_id"), "evaluation_cases", ["external_id"])
    op.create_index(op.f("ix_evaluation_cases_language"), "evaluation_cases", ["language"])
    op.create_index(op.f("ix_evaluation_cases_workspace_id"), "evaluation_cases", ["workspace_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("modes_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_runs_created_by_user_id"),
        "evaluation_runs",
        ["created_by_user_id"],
    )
    op.create_index(op.f("ix_evaluation_runs_workspace_id"), "evaluation_runs", ["workspace_id"])

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_case_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("actual_route", sa.String(length=80), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("citations_json", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("scores_json", sa.Text(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_case_id"], ["evaluation_cases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_results_evaluation_case_id"),
        "evaluation_results",
        ["evaluation_case_id"],
    )
    op.create_index(
        op.f("ix_evaluation_results_evaluation_run_id"),
        "evaluation_results",
        ["evaluation_run_id"],
    )
    op.create_index(op.f("ix_evaluation_results_language"), "evaluation_results", ["language"])
    op.create_index(op.f("ix_evaluation_results_mode"), "evaluation_results", ["mode"])
    op.create_index(
        op.f("ix_evaluation_results_workspace_id"),
        "evaluation_results",
        ["workspace_id"],
    )

    op.create_table(
        "evaluation_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_run_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False),
        sa.Column("metric_name", sa.String(length=120), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["evaluation_run_id"], ["evaluation_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evaluation_metrics_evaluation_run_id"),
        "evaluation_metrics",
        ["evaluation_run_id"],
    )
    op.create_index(op.f("ix_evaluation_metrics_language"), "evaluation_metrics", ["language"])
    op.create_index(
        op.f("ix_evaluation_metrics_metric_name"),
        "evaluation_metrics",
        ["metric_name"],
    )
    op.create_index(op.f("ix_evaluation_metrics_mode"), "evaluation_metrics", ["mode"])
    op.create_index(
        op.f("ix_evaluation_metrics_workspace_id"),
        "evaluation_metrics",
        ["workspace_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_metrics_workspace_id"), table_name="evaluation_metrics")
    op.drop_index(op.f("ix_evaluation_metrics_mode"), table_name="evaluation_metrics")
    op.drop_index(op.f("ix_evaluation_metrics_metric_name"), table_name="evaluation_metrics")
    op.drop_index(op.f("ix_evaluation_metrics_language"), table_name="evaluation_metrics")
    op.drop_index(op.f("ix_evaluation_metrics_evaluation_run_id"), table_name="evaluation_metrics")
    op.drop_table("evaluation_metrics")
    op.drop_index(op.f("ix_evaluation_results_workspace_id"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_mode"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_language"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_evaluation_run_id"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_evaluation_case_id"), table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index(op.f("ix_evaluation_runs_workspace_id"), table_name="evaluation_runs")
    op.drop_index(op.f("ix_evaluation_runs_created_by_user_id"), table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index(op.f("ix_evaluation_cases_workspace_id"), table_name="evaluation_cases")
    op.drop_index(op.f("ix_evaluation_cases_language"), table_name="evaluation_cases")
    op.drop_index(op.f("ix_evaluation_cases_external_id"), table_name="evaluation_cases")
    op.drop_table("evaluation_cases")
