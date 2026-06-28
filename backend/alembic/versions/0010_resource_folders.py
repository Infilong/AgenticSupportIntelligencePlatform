"""add resource folders

Revision ID: 0010_resource_folders
Revises: 0009_audit_logs
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_resource_folders"
down_revision: str | None = "0009_audit_logs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resource_folders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("parent_folder_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_folder_id"], ["resource_folders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_resource_folders_created_by_user_id"),
        "resource_folders",
        ["created_by_user_id"],
    )
    op.create_index(
        op.f("ix_resource_folders_parent_folder_id"),
        "resource_folders",
        ["parent_folder_id"],
    )
    op.create_index(
        op.f("ix_resource_folders_resource_type"),
        "resource_folders",
        ["resource_type"],
    )
    op.create_index(
        op.f("ix_resource_folders_workspace_id"),
        "resource_folders",
        ["workspace_id"],
    )
    op.create_index(
        "ix_resource_folders_workspace_type",
        "resource_folders",
        ["workspace_id", "resource_type"],
    )

    op.add_column("knowledge_documents", sa.Column("folder_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_documents_folder_id_resource_folders",
        "knowledge_documents",
        "resource_folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_knowledge_documents_folder_id"),
        "knowledge_documents",
        ["folder_id"],
    )
    op.create_index(
        "ix_knowledge_documents_workspace_folder",
        "knowledge_documents",
        ["workspace_id", "folder_id"],
    )

    op.add_column("datasets", sa.Column("folder_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_datasets_folder_id_resource_folders",
        "datasets",
        "resource_folders",
        ["folder_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_datasets_folder_id"), "datasets", ["folder_id"])
    op.create_index("ix_datasets_workspace_folder", "datasets", ["workspace_id", "folder_id"])


def downgrade() -> None:
    op.drop_index("ix_datasets_workspace_folder", table_name="datasets")
    op.drop_index(op.f("ix_datasets_folder_id"), table_name="datasets")
    op.drop_constraint("fk_datasets_folder_id_resource_folders", "datasets", type_="foreignkey")
    op.drop_column("datasets", "folder_id")

    op.drop_index("ix_knowledge_documents_workspace_folder", table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_folder_id"), table_name="knowledge_documents")
    op.drop_constraint(
        "fk_knowledge_documents_folder_id_resource_folders",
        "knowledge_documents",
        type_="foreignkey",
    )
    op.drop_column("knowledge_documents", "folder_id")

    op.drop_index("ix_resource_folders_workspace_type", table_name="resource_folders")
    op.drop_index(op.f("ix_resource_folders_workspace_id"), table_name="resource_folders")
    op.drop_index(op.f("ix_resource_folders_resource_type"), table_name="resource_folders")
    op.drop_index(op.f("ix_resource_folders_parent_folder_id"), table_name="resource_folders")
    op.drop_index(op.f("ix_resource_folders_created_by_user_id"), table_name="resource_folders")
    op.drop_table("resource_folders")
