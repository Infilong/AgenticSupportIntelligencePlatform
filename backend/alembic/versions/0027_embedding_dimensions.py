"""Allow semantic embedding dimensions while preserving existing vectors."""

from alembic import op

revision = "0027_embedding_dimensions"
down_revision = "0026_model_call_reservations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("ALTER TABLE embeddings ALTER COLUMN vector TYPE vector USING vector::vector")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    # Keep admission and conversion under the same lock: concurrent inserts cannot race the check.
    op.execute("LOCK TABLE embeddings IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM embeddings WHERE vector_dims(vector) <> 16) THEN
                RAISE EXCEPTION 'Cannot downgrade embeddings: non-16-dimensional vectors exist';
            END IF;
        END $$;
    """)
    op.execute(
        "ALTER TABLE embeddings ALTER COLUMN vector TYPE vector(16) USING vector::vector(16)"
    )
