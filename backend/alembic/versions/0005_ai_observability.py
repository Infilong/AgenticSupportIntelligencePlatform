"""create ai observability tables

Revision ID: 0005_ai_observability
Revises: 0004_retrieval_traces
Create Date: 2026-06-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_ai_observability"
down_revision: str | None = "0004_retrieval_traces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    supported_language = postgresql.ENUM(
        "en", "ja", "zh", name="supported_language", create_type=False
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE ai_run_status AS ENUM ('succeeded', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )
    ai_run_status = postgresql.ENUM(
        "succeeded", "failed", name="ai_run_status", create_type=False
    )

    op.create_table(
        "model_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False),
        sa.Column("prompt_token_cost_per_1k", sa.Float(), nullable=False),
        sa.Column("completion_token_cost_per_1k", sa.Float(), nullable=False),
        sa.Column("max_context_tokens", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_configs_purpose"), "model_configs", ["purpose"])
    op.create_index(op.f("ix_model_configs_workspace_id"), "model_configs", ["workspace_id"])

    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workspace_id", "name", "language", "version", name="uq_prompt_template_version"
        ),
    )
    op.create_index(
        op.f("ix_prompt_templates_workspace_id"), "prompt_templates", ["workspace_id"]
    )

    op.create_table(
        "ai_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), nullable=True),
        sa.Column("graph_step_id", sa.Uuid(), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False),
        sa.Column("language", supported_language, nullable=False),
        sa.Column("prompt_template_id", sa.Uuid(), nullable=True),
        sa.Column("prompt_version", sa.Integer(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False),
        sa.Column("status", ai_run_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["prompt_template_id"], ["prompt_templates.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_runs_graph_run_id"), "ai_runs", ["graph_run_id"])
    op.create_index(op.f("ix_ai_runs_graph_step_id"), "ai_runs", ["graph_step_id"])
    op.create_index(op.f("ix_ai_runs_purpose"), "ai_runs", ["purpose"])
    op.create_index(op.f("ix_ai_runs_workspace_id"), "ai_runs", ["workspace_id"])

    op.create_table(
        "cache_entries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("cache_key", sa.String(length=200), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False),
        sa.Column("language", supported_language, nullable=True),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "cache_key", "purpose", name="uq_cache_entry_key"),
    )
    op.create_index(op.f("ix_cache_entries_workspace_id"), "cache_entries", ["workspace_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_cache_entries_workspace_id"), table_name="cache_entries")
    op.drop_table("cache_entries")
    op.drop_index(op.f("ix_ai_runs_workspace_id"), table_name="ai_runs")
    op.drop_index(op.f("ix_ai_runs_purpose"), table_name="ai_runs")
    op.drop_index(op.f("ix_ai_runs_graph_step_id"), table_name="ai_runs")
    op.drop_index(op.f("ix_ai_runs_graph_run_id"), table_name="ai_runs")
    op.drop_table("ai_runs")
    op.drop_index(op.f("ix_prompt_templates_workspace_id"), table_name="prompt_templates")
    op.drop_table("prompt_templates")
    op.drop_index(op.f("ix_model_configs_workspace_id"), table_name="model_configs")
    op.drop_index(op.f("ix_model_configs_purpose"), table_name="model_configs")
    op.drop_table("model_configs")
    postgresql.ENUM(name="ai_run_status").drop(op.get_bind(), checkfirst=True)
