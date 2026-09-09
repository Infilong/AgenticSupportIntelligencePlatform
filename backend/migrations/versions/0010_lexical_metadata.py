"""Add and backfill versioned BM25 metadata without changing source evidence."""

import re
import unicodedata
from collections import Counter

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0010_lexical_metadata"
down_revision = "0009_attempts"
branch_labels = None
depends_on = None


def frozen_frequencies(text):
    # Frozen v1 recipe: migrations must not import a future application's tokenizer.
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens = []
    for match in re.finditer(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", normalized):
        token = match.group()
        tokens.append(token)
        if "-" in token or "_" in token:
            tokens.extend(re.split("[-_]", token))
    for match in re.finditer(r"[\u3040-\u30ff\u3400-\u9fff]+", normalized):
        run = match.group()
        tokens.extend(run[i : i + 2] for i in range(max(1, len(run) - 1)))
    return dict(Counter(tokens))


def upgrade():
    op.add_column("document_chunks", sa.Column("lexical_frequencies", JSONB, nullable=True))
    op.add_column("document_chunks", sa.Column("lexical_length", sa.Integer, nullable=True))
    op.add_column("document_chunks", sa.Column("lexical_version", sa.String(64), nullable=True))
    table = sa.table(
        "document_chunks",
        sa.column("id", sa.Uuid),
        sa.column("text", sa.Text),
        sa.column("lexical_frequencies", JSONB),
        sa.column("lexical_length", sa.Integer),
        sa.column("lexical_version", sa.String),
    )
    connection, after = op.get_bind(), None
    while True:
        query = sa.select(table.c.id, table.c.text).order_by(table.c.id).limit(500)
        if after is not None:
            query = query.where(table.c.id > after)
        rows = connection.execute(query).all()
        if not rows:
            break
        for row in rows:
            counts = frozen_frequencies(row.text)
            connection.execute(
                table.update()
                .where(table.c.id == row.id)
                .values(
                    lexical_frequencies=counts,
                    lexical_length=sum(counts.values()),
                    lexical_version="nfkc-identifiers-cjk-bigrams-v1",
                )
            )
        after = rows[-1].id
    op.create_check_constraint(
        "ck_chunk_lexical_length", "document_chunks", "lexical_length IS NULL OR lexical_length >= 0"
    )


def downgrade():
    op.drop_constraint("ck_chunk_lexical_length", "document_chunks", type_="check")
    op.drop_column("document_chunks", "lexical_version")
    op.drop_column("document_chunks", "lexical_length")
    op.drop_column("document_chunks", "lexical_frequencies")
