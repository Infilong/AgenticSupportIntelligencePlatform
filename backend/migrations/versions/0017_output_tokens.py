"""Record generated tokens and recover available historical measurements."""

import sqlalchemy as sa
from alembic import op

revision = "0017_output_tokens"
down_revision = "0016_generation_comparisons"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("model_calls", sa.Column("output_tokens", sa.Integer(), nullable=True))
    # Match workspace and dispatch identity; never infer missing measurements as zero.
    for table, request in [
        ("development_handoffs", "generation_request"),
        ("generation_pipelines", "request"),
    ]:
        op.execute(
            sa.text(f"""
            UPDATE model_calls AS m
            SET output_tokens = (h.response->'usage'->>'output_tokens')::integer
            FROM {table} AS h
            WHERE m.workspace_id = h.workspace_id
              AND m.id::text = h.{request}->>'call_id'
              AND m.revision = h.request_hash
              AND m.provider = 'local_ollama'
              AND jsonb_typeof(h.response->'usage'->'output_tokens') = 'number'
              AND (h.response->'usage'->>'output_tokens') ~ '^[0-9]{{1,9}}$'
        """)
        )


def downgrade():
    op.drop_column("model_calls", "output_tokens")
