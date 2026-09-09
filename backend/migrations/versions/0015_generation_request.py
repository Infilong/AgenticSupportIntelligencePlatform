"""Record exact development requests without inventing historical prompt records."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0015_generation_request"
down_revision = "0014_evaluation_records"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("development_handoffs", sa.Column("generation_request", postgresql.JSONB()))
    op.add_column("development_handoffs", sa.Column("request_hash", sa.String(64)))
    op.create_check_constraint(
        "handoff_request_pair", "development_handoffs",
        "(generation_request IS NULL) = (request_hash IS NULL)",
    )


def downgrade():
    op.drop_constraint("handoff_request_pair", "development_handoffs", type_="check")
    op.drop_column("development_handoffs", "request_hash")
    op.drop_column("development_handoffs", "generation_request")
