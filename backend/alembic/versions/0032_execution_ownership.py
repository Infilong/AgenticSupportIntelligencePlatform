"""Persist ownership provenance without assigning it to legacy provider history."""

import sqlalchemy as sa

from alembic import op

revision = "0032_execution_ownership"
down_revision = "0031_graph_step_sequence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ai_runs", sa.Column("execution_id", sa.Uuid(), nullable=True))
    op.add_column("ai_runs", sa.Column("execution_protocol", sa.String(32), nullable=True))
    op.create_check_constraint("ck_ai_run_execution_protocol", "ai_runs",
        "(execution_id IS NULL AND execution_protocol IS NULL) OR "
        "(execution_id IS NOT NULL AND execution_protocol IS NOT NULL "
        "AND execution_protocol = 'pg-session-v1')")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE ai_runs IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text(
        "SELECT EXISTS (SELECT 1 FROM ai_runs WHERE execution_id IS NOT NULL)"
    )):
        raise RuntimeError("Cannot downgrade while execution ownership history exists")
    op.drop_constraint("ck_ai_run_execution_protocol", "ai_runs", type_="check")
    op.drop_column("ai_runs", "execution_protocol")
    op.drop_column("ai_runs", "execution_id")
