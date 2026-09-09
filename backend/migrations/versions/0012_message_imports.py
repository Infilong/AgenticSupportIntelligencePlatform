"""Saved customer messages with bounded import provenance and labels."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0012_message_imports"
down_revision = "0011_retrieval_stages"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "message_imports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(160), nullable=False),
        sa.Column("submission_key", sa.String(100), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("workspace_id", "id", name="uq_import_workspace"),
        sa.UniqueConstraint("workspace_id", "submission_key", name="uq_import_submission"),
    )
    op.add_column(
        "support_messages", sa.Column("labels", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))
    )
    op.add_column("support_messages", sa.Column("import_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_message_import",
        "support_messages",
        "message_imports",
        ["workspace_id", "import_id"],
        ["workspace_id", "id"],
    )


def downgrade():
    op.drop_constraint("fk_message_import", "support_messages", type_="foreignkey")
    op.drop_column("support_messages", "import_id")
    op.drop_column("support_messages", "labels")
    op.drop_table("message_imports")
