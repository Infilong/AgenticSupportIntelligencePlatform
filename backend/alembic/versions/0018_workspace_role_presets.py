"""add workspace role presets

Revision ID: 0018_workspace_role_presets
Revises: 0017_airun_model_cfg
Create Date: 2026-06-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0018_workspace_role_presets"
down_revision: str | None = "0017_airun_model_cfg"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for role in ("developer", "reviewer", "viewer"):
            op.execute(f"ALTER TYPE workspacerole ADD VALUE IF NOT EXISTS '{role}'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without rebuilding the type.
    pass
