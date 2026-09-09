"""Bounded SQL BM25 over the same active population used for vector search."""

from sqlalchemy import Float, Integer, Text, cast, func, or_, select, true
from sqlalchemy.dialects.postgresql import ARRAY

from app.modules.knowledge.lexical import LEXICAL_VERSION, query_terms
from app.modules.knowledge.models import Chunk
from app.modules.knowledge.population import active_chunks

K1, B = 1.2, 0.75


class LexicalIndexIncomplete(RuntimeError):
    pass


def population(workspace_id):
    return (
        active_chunks(workspace_id)
        .with_only_columns(
            Chunk.id,
            Chunk.lexical_frequencies.label("tf"),
            Chunk.lexical_length.label("dl"),
            Chunk.lexical_version.label("recipe"),
        )
        .cte("active_lexical")
        .prefix_with("MATERIALIZED")
    )


def ranking_query(active, terms, limit):
    terms_array = cast(terms, ARRAY(Text))
    words = func.unnest(terms_array).table_valued("term").render_derived()
    stats = select(func.count().label("n"), func.avg(active.c.dl).label("avgdl")).cte("stats")
    matches = (
        select(
            active.c.id,
            active.c.dl,
            words.c.term,
            cast(active.c.tf[words.c.term].astext, Integer).label("frequency"),
        )
        .select_from(active.join(words, true()))
        .where(
            active.c.tf.has_any(terms_array),
            active.c.tf.has_key(words.c.term),
        )
        .cte("matches")
    )
    df = select(matches.c.term, func.count().label("df")).group_by(matches.c.term).cte("df")
    idf = func.ln(1 + (stats.c.n - df.c.df + 0.5) / (df.c.df + 0.5))
    norm = K1 * (1 - B + B * matches.c.dl / func.nullif(stats.c.avgdl, 0))
    score = func.sum(idf * (matches.c.frequency * (K1 + 1)) / (matches.c.frequency + norm))
    return (
        select(matches.c.id, cast(score, Float).label("score"))
        .select_from(matches.join(df, matches.c.term == df.c.term).join(stats, true()))
        .group_by(matches.c.id)
        .order_by(score.desc(), matches.c.id)
        .limit(limit)
    )


def candidates(db, workspace_id, query, limit=20):
    if not 1 <= limit <= 20:
        raise ValueError("BM25 candidate limit must be 1–20")
    terms = query_terms(query)
    active = population(workspace_id)
    missing = db.scalar(
        select(func.count())
        .select_from(active)
        .where(
            or_(
                active.c.recipe.is_(None),
                active.c.recipe != LEXICAL_VERSION,
                active.c.tf.is_(None),
                func.jsonb_typeof(active.c.tf) != "object",
                active.c.dl.is_(None),
            )
        )
    )
    if missing:
        raise LexicalIndexIncomplete("Active sources require lexical metadata backfill")
    if not terms:
        return []
    return [
        {"chunk_id": str(row.id), "bm25_score": row.score, "bm25_rank": rank}
        for rank, row in enumerate(db.execute(ranking_query(active, terms, limit)), 1)
    ]
