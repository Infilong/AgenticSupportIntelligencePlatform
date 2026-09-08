"""Allow model-call admission for evaluation baselines without synthetic graph runs."""

import sqlalchemy as sa

from alembic import op

revision = "0030_evaluation_reservations"
down_revision = "0029_retrieval_outcome"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("model_call_reservations", sa.Column("evaluation_run_id", sa.Uuid()))
    op.create_foreign_key("fk_reservation_evaluation", "model_call_reservations",
                          "evaluation_runs", ["evaluation_run_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_model_call_reservations_evaluation_run_id", "model_call_reservations",
                    ["evaluation_run_id"])
    op.alter_column("model_call_reservations", "graph_run_id", nullable=True)
    op.create_check_constraint("ck_reservation_context", "model_call_reservations",
                               "(graph_run_id IS NULL) <> (evaluation_run_id IS NULL)")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE model_call_reservations IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text(
        "SELECT EXISTS (SELECT 1 FROM model_call_reservations WHERE evaluation_run_id IS NOT NULL)"
    )):
        raise RuntimeError("Cannot downgrade while evaluation reservations exist")
    op.drop_constraint("ck_reservation_context", "model_call_reservations", type_="check")
    op.alter_column("model_call_reservations", "graph_run_id", nullable=False)
    op.drop_index("ix_model_call_reservations_evaluation_run_id",
                  table_name="model_call_reservations")
    op.drop_constraint("fk_reservation_evaluation", "model_call_reservations", type_="foreignkey")
    op.drop_column("model_call_reservations", "evaluation_run_id")
