"""Add explicit hierarchy roles without converting legacy memberships."""

from alembic import op

revision = "0033_admin_operator_roles"
down_revision = "0032_execution_ownership"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE workspacerole ADD VALUE IF NOT EXISTS 'admin'")
    op.execute("ALTER TYPE workspacerole ADD VALUE IF NOT EXISTS 'operator'")


def downgrade() -> None:
    # PostgreSQL cannot remove enum labels without replacing the type. Preserve data
    # and reject downgrade rather than relabeling authority or breaking old code.
    raise RuntimeError("Role additions require forward repair or a verified backup restore")
