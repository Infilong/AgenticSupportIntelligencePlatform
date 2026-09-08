"""Persist workspace-scoped model-call budget admission."""

import sqlalchemy as sa

from alembic import op

revision = "0026_model_call_reservations"
down_revision = "0025_ai_run_prompt_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "model_call_reservations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("graph_run_id", sa.Uuid(), sa.ForeignKey("graph_runs.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("ai_run_id", sa.Uuid(), sa.ForeignKey("ai_runs.id", ondelete="SET NULL"),
                  nullable=True, unique=True),
        sa.Column("purpose", sa.String(120), nullable=False),
        sa.Column("estimated_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("denial_reason", sa.String(80)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finalized_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("estimated_tokens >= 0", name="ck_reservation_tokens"),
        sa.CheckConstraint("estimated_cost >= 0", name="ck_reservation_cost"),
        sa.CheckConstraint("status IN ('reserved','consumed','released','denied')",
                           name="ck_reservation_status"),
    )
    for column in ("workspace_id", "graph_run_id"):
        op.create_index(f"ix_model_call_reservations_{column}", "model_call_reservations", [column])


def downgrade() -> None:
    op.drop_table("model_call_reservations")
