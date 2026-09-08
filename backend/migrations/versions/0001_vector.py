"""Enable PostgreSQL vector support for the isolated rebuild database."""

from alembic import op

revision = "0001_vector"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    # Extension can be shared by later objects. Rollback does not destroy it or their data.
    pass
