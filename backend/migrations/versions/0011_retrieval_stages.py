"""Retain bounded candidate-stage evidence; older traces remain explicitly unstaged."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0011_retrieval_stages"
down_revision = "0010_lexical_metadata"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "retrieval_traces", sa.Column("stages", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb"))
    )


def downgrade():
    op.drop_column("retrieval_traces", "stages")
