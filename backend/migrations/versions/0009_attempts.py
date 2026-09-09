"""Immutable linked processing attempts; originals and earlier reviews remain intact."""

import sqlalchemy as sa
from alembic import op

revision = "0009_attempts"
down_revision = "0008_reviews"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("support_runs", sa.Column("parent_run_id", sa.Uuid))
    op.add_column(
        "support_runs", sa.Column("creator_id", sa.Uuid, sa.ForeignKey("users.id", name="fk_run_creator"))
    )
    op.add_column("support_runs", sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"))
    op.add_column(
        "support_runs", sa.Column("attempt_kind", sa.String(16), nullable=False, server_default="initial")
    )
    op.add_column("support_runs", sa.Column("input_text", sa.Text))
    op.add_column("support_runs", sa.Column("clarification", sa.Text))
    op.add_column("support_runs", sa.Column("submission_key", sa.String(100)))
    op.add_column("support_runs", sa.Column("submission_hash", sa.String(64)))
    op.execute("""UPDATE support_runs r SET creator_id=m.actor_id, input_text=m.original
                  FROM support_messages m WHERE m.id=r.message_id AND m.workspace_id=r.workspace_id""")
    op.alter_column("support_runs", "creator_id", nullable=False)
    op.alter_column("support_runs", "input_text", nullable=False)
    op.create_unique_constraint("uq_run_message", "support_runs", ["workspace_id", "message_id", "id"])
    op.create_unique_constraint(
        "uq_run_attempt", "support_runs", ["workspace_id", "message_id", "attempt_number"]
    )
    op.create_unique_constraint("uq_run_submission", "support_runs", ["workspace_id", "submission_key"])
    op.create_foreign_key(
        "fk_run_parent",
        "support_runs",
        "support_runs",
        ["workspace_id", "message_id", "parent_run_id"],
        ["workspace_id", "message_id", "id"],
    )
    op.create_check_constraint("run_attempt_number", "support_runs", "attempt_number BETWEEN 1 AND 10")
    op.create_check_constraint("run_input_size", "support_runs", "char_length(input_text) BETWEEN 1 AND 1000")
    op.create_check_constraint(
        "run_attempt_kind",
        "support_runs",
        "(attempt_kind='initial' AND parent_run_id IS NULL AND attempt_number=1) OR "
        "(attempt_kind IN ('retry','clarify') AND parent_run_id IS NOT NULL AND attempt_number>1)",
    )


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT count(*) FROM support_runs WHERE parent_run_id IS NOT NULL")):
        raise RuntimeError("Linked attempts exist; restore a verified backup instead of discarding lineage")
    for name in ("run_attempt_kind", "run_input_size", "run_attempt_number"):
        op.drop_constraint(name, "support_runs", type_="check")
    op.drop_constraint("fk_run_parent", "support_runs", type_="foreignkey")
    for name in ("uq_run_submission", "uq_run_attempt", "uq_run_message"):
        op.drop_constraint(name, "support_runs", type_="unique")
    op.drop_constraint("fk_run_creator", "support_runs", type_="foreignkey")
    for name in (
        "submission_hash",
        "submission_key",
        "clarification",
        "input_text",
        "attempt_kind",
        "attempt_number",
        "creator_id",
        "parent_run_id",
    ):
        op.drop_column("support_runs", name)
