"""Separate execution/outcome and preserve attributed review decisions."""

import sqlalchemy as sa
from alembic import op

revision = "0008_reviews"
down_revision = "0007_support"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("support_runs", sa.Column("outcome", sa.String(32)))
    op.add_column(
        "support_runs", sa.Column("review_kind", sa.String(24), nullable=False, server_default="ordinary")
    )
    op.add_column("support_runs", sa.Column("review_version", sa.Integer, nullable=False, server_default="0"))
    op.add_column("support_runs", sa.Column("reviewed_response", sa.Text))
    op.add_column("support_runs", sa.Column("drafted_at", sa.DateTime(timezone=True)))
    op.drop_constraint("support_run_state", "support_runs", type_="check")
    op.execute("""UPDATE support_runs SET
        review_kind = CASE WHEN state = 'draft' THEN 'unclassified' ELSE 'ordinary' END,
        outcome = CASE state WHEN 'draft' THEN 'grounded_draft'
            WHEN 'clarification' THEN 'clarification_needed'
            WHEN 'insufficient_evidence' THEN 'insufficient_evidence' ELSE NULL END,
        drafted_at = CASE WHEN state = 'draft' THEN finished_at ELSE NULL END,
        finished_at = CASE WHEN state = 'draft' THEN NULL ELSE finished_at END,
        state = CASE state WHEN 'draft' THEN 'awaiting_review'
            WHEN 'waiting_development' THEN 'waiting_for_input'
            WHEN 'clarification' THEN 'completed' WHEN 'insufficient_evidence' THEN 'completed'
            ELSE state END""")
    op.create_check_constraint(
        "support_run_state",
        "support_runs",
        "state IN ('queued','waiting_for_input','awaiting_review','completed','rejected','cancelled')",
    )
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("workspace_id", sa.Uuid, nullable=False),
        sa.Column("run_id", sa.Uuid, nullable=False),
        sa.Column("actor_id", sa.Uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("draft_hash", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("response", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id", "run_id"], ["support_runs.workspace_id", "support_runs.id"]),
        sa.UniqueConstraint("workspace_id", "run_id", name="uq_review_run"),
    )


def downgrade():
    # Do not discard reviewed responses/decisions silently in a rollback.
    connection = op.get_bind()
    if connection.scalar(sa.text("SELECT count(*) FROM review_decisions")):
        raise RuntimeError(
            "Review decisions exist; restore a verified backup instead of losing review history"
        )
    op.drop_table("review_decisions")
    op.drop_constraint("support_run_state", "support_runs", type_="check")
    op.execute("""UPDATE support_runs SET state = CASE
        WHEN state = 'awaiting_review' THEN 'draft'
        WHEN state = 'waiting_for_input' THEN 'waiting_development'
        WHEN outcome = 'clarification_needed' THEN 'clarification'
        WHEN outcome = 'insufficient_evidence' THEN 'insufficient_evidence' ELSE state END,
        finished_at = COALESCE(finished_at, drafted_at)""")
    op.create_check_constraint(
        "support_run_state",
        "support_runs",
        "state IN ('queued','waiting_development','draft','clarification',"
        "'insufficient_evidence','cancelled')",
    )
    for name in ("drafted_at", "reviewed_response", "review_version", "review_kind", "outcome"):
        op.drop_column("support_runs", name)
