"""Distinguish failed retrieval from a successful search with no matching sources."""

import sqlalchemy as sa

from alembic import op

revision = "0029_retrieval_outcome"
down_revision = "0028_ai_attempt_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.add_column("retrieval_traces", sa.Column("outcome", sa.String(20),
                  nullable=False, server_default="unknown"))
    op.add_column("retrieval_traces", sa.Column("error_code", sa.String(80), nullable=True))


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE retrieval_traces IN ACCESS EXCLUSIVE MODE")
    op.execute("""DO $$ BEGIN
        IF EXISTS (SELECT 1 FROM retrieval_traces WHERE outcome IN ('failed', 'pending')) THEN
            RAISE EXCEPTION 'Cannot downgrade retrieval outcomes with failed or pending traces';
        END IF;
    END $$;""")
    op.drop_column("retrieval_traces", "error_code")
    op.drop_column("retrieval_traces", "outcome")
