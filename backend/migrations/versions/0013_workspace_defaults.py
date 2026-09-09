"""Default language for new manual messages; existing input languages stay unchanged."""

import sqlalchemy as sa
from alembic import op

revision = "0013_workspace_defaults"
down_revision = "0012_message_imports"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "workspaces", sa.Column("default_language", sa.String(2), nullable=False, server_default="en")
    )
    op.create_check_constraint(
        "workspace_default_language", "workspaces", "default_language IN ('en','ja','zh')"
    )


def downgrade():
    op.drop_constraint("workspace_default_language", "workspaces", type_="check")
    op.drop_column("workspaces", "default_language")
