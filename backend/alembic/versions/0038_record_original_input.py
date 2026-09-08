"""Preserve typed original inputs without fabricating historical source metadata."""

import sqlalchemy as sa

from alembic import op

revision = "0038_record_original_input"
down_revision = "0037_retire_legacy_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.add_column("support_tasks", sa.Column("input_envelope_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE support_tasks IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text(
            "SELECT EXISTS (SELECT 1 FROM support_tasks WHERE input_envelope_json IS NOT NULL)")):
        raise RuntimeError("Cannot discard original record data; use forward repair or restore")
    op.drop_column("support_tasks", "input_envelope_json")
