"""Preserve bounded originals and durable document ingestion state."""
import sqlalchemy as sa

from alembic import op

revision = "0040_knowledge_uploads"
down_revision = "0039_record_clarification"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.create_table("knowledge_uploads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"),
                  nullable=False),
        sa.Column("document_version_id", sa.Uuid(),
                  sa.ForeignKey("document_versions.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("language", sa.String(2), nullable=False),
        sa.Column("original_sha256", sa.String(64), nullable=False),
        sa.Column("original_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("extraction_metadata", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "request_key", name="uq_knowledge_upload_request"),
        sa.CheckConstraint("length(original_bytes) BETWEEN 1 AND 20971520",
                           name="ck_knowledge_upload_size"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_knowledge_upload_attempts"),
        sa.CheckConstraint("state IN ('uploaded','extracting','chunking','embedding',"
                           "'ready','failed','requires_ocr')", name="ck_knowledge_upload_state"),
        sa.CheckConstraint("state != 'ready' OR (document_version_id IS NOT NULL "
                           "AND extracted_text IS NOT NULL AND length(extracted_text) > 0)",
                           name="ck_knowledge_upload_ready"),
    )
    op.create_index("ix_knowledge_uploads_workspace_id", "knowledge_uploads", ["workspace_id"])
    op.create_index("ix_knowledge_uploads_state", "knowledge_uploads", ["state"])


def downgrade():
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE knowledge_uploads IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM knowledge_uploads)")):
        raise RuntimeError("Cannot discard uploaded originals; use forward repair or restore")
    op.drop_table("knowledge_uploads")
