"""Represent durable pending and uncertain model attempts honestly."""

from alembic import op

revision = "0028_ai_attempt_status"
down_revision = "0027_embedding_dimensions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE ai_run_status ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE ai_run_status ADD VALUE IF NOT EXISTS 'uncertain'")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE ai_runs IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM ai_runs WHERE status::text IN ('pending', 'uncertain')) THEN
                RAISE EXCEPTION 'Cannot downgrade AI ledger: unresolved attempts exist';
            END IF;
        END $$;
    """)
    op.execute("ALTER TYPE ai_run_status RENAME TO ai_run_status_expanded")
    op.execute("CREATE TYPE ai_run_status AS ENUM ('succeeded', 'failed')")
    op.execute("ALTER TABLE ai_runs ALTER COLUMN status TYPE ai_run_status "
               "USING status::text::ai_run_status")
    op.execute("DROP TYPE ai_run_status_expanded")
