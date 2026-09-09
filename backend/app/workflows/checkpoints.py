"""Explicit supported checkpointer setup and per-run dedicated database sessions."""

from contextlib import contextmanager

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from psycopg.rows import dict_row

from app.core.settings import Settings
from app.db.engine import make_engine
from app.jobs.contracts import RetryableJobError


def connect(engine):
    url = engine.url
    return psycopg.connect(
        **url.translate_connect_args(username="user", database="dbname"),
        **dict(url.query),
        autocommit=True,
        row_factory=dict_row,
    )


def saver(connection):
    # Graph state consists only of primitive dictionaries/lists; do not permit arbitrary classes.
    return PostgresSaver(connection, serde=JsonPlusSerializer(allowed_msgpack_modules=[]))


def setup(engine):
    with connect(engine) as connection:
        saver(connection).setup()


@contextmanager
def locked_graph(engine, run_id):
    try:
        # Closing this dedicated session releases its advisory lock even after connection errors.
        with connect(engine) as connection:
            key = int.from_bytes(run_id.bytes[:8], "big", signed=True)
            locked = connection.execute("SELECT pg_try_advisory_lock(%s) AS locked", (key,)).fetchone()[
                "locked"
            ]
            if not locked:
                raise RetryableJobError("Another execution owns this graph")
            yield saver(connection)
    except (psycopg.OperationalError, psycopg.InterfaceError) as error:
        raise RetryableJobError("Temporary checkpoint connection failure") from error


if __name__ == "__main__":
    engine = make_engine(Settings())
    try:
        setup(engine)
        print("Supported LangGraph checkpoint tables initialized.")
    finally:
        engine.dispose()
