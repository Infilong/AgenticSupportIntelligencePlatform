"""Keep user clarification separate from administrator retry instructions."""

import sqlalchemy as sa

from alembic import op

revision = "0039_record_clarification"
down_revision = "0038_record_original_input"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.add_column("task_attempts", sa.Column("clarification_reply", sa.Text(), nullable=True))


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE task_attempts IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text(
            "SELECT EXISTS (SELECT 1 FROM task_attempts WHERE clarification_reply IS NOT NULL)")):
        raise RuntimeError("Cannot discard clarification replies; use forward repair or restore")
    op.drop_column("task_attempts", "clarification_reply")
