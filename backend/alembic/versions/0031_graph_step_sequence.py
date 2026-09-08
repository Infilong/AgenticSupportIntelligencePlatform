"""Record new graph step order without inventing legacy execution history."""

import sqlalchemy as sa

from alembic import op

revision = "0031_graph_step_sequence"
down_revision = "0030_evaluation_reservations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("graph_steps", sa.Column("sequence", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_graph_step_sequence", "graph_steps",
                                ["graph_run_id", "sequence"])
    op.create_check_constraint("ck_graph_step_sequence_positive", "graph_steps", "sequence > 0")


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '10s'")
    op.execute("LOCK TABLE graph_steps IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().scalar(sa.text(
        "SELECT EXISTS (SELECT 1 FROM graph_steps WHERE sequence IS NOT NULL)"
    )):
        raise RuntimeError("Cannot downgrade while sequenced graph history exists")
    op.drop_constraint("ck_graph_step_sequence_positive", "graph_steps", type_="check")
    op.drop_constraint("uq_graph_step_sequence", "graph_steps", type_="unique")
    op.drop_column("graph_steps", "sequence")
