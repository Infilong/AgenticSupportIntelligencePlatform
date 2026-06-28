"""add agent config folders

Revision ID: 0022_agent_config_folders
Revises: 0021_evaluation_run_agent_id
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022_agent_config_folders"
down_revision: str | None = "0021_evaluation_run_agent_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_configs", sa.Column("folder_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_agent_configs_folder_id"), "agent_configs", ["folder_id"])
    op.create_index(
        "ix_agent_configs_workspace_folder", "agent_configs", ["workspace_id", "folder_id"]
    )
    op.create_foreign_key(
        op.f("fk_agent_configs_folder_id_resource_folders"),
        "agent_configs",
        "resource_folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_agent_configs_folder_id_resource_folders"),
        "agent_configs",
        type_="foreignkey",
    )
    op.drop_index("ix_agent_configs_workspace_folder", table_name="agent_configs")
    op.drop_index(op.f("ix_agent_configs_folder_id"), table_name="agent_configs")
    op.drop_column("agent_configs", "folder_id")
