"""Upgrade populated legacy chunks transactionally, without rewriting evidence."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, select, text
from sqlalchemy.orm import Session

from app.modules.knowledge.ingestion import SPACE
from app.modules.knowledge.lexical import LEXICAL_VERSION, frequencies
from app.modules.knowledge.models import Chunk, Document
from tests.integration.test_knowledge import add_version


def migrate(engine, target, upgrade=True):
    with engine.begin() as connection:
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.attributes["connection"] = connection
        (command.upgrade if upgrade else command.downgrade)(config, target)


def evidence_rows(engine):
    with engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT id, version_id, text, start_offset, end_offset, embedding::text "
                "FROM document_chunks ORDER BY id"
            )
        ).all()


def test_backfill_batches_preserve_evidence_and_recover_from_interruption(system):
    lines = [f"Policy {index}: ＥＲＲＯＲ－８４２２ 政策政策\n" for index in range(503)] + ["！！！\n"]
    version = add_version(system, "".join(lines).encode())
    engine = system["engine"]
    with Session(engine) as db, db.begin():
        db.get(Document, version.document_id).active_version_id = version.id
        offset = 0
        for index, line in enumerate(lines):
            db.add(
                Chunk(
                    workspace_id=system["workspace"],
                    version_id=version.id,
                    ordinal=index,
                    text=line,
                    start_offset=offset,
                    end_offset=offset + len(line),
                    section="Policy",
                    token_count=10,
                    embedding=[1.0] + [0.0] * 383,
                    embedding_space=SPACE,
                    lexical_terms=[],
                )
            )
            offset += len(line)
    before = evidence_rows(engine)
    migrate(engine, "0009_attempts", upgrade=False)
    writes = 0

    def interrupt(connection, cursor, statement, parameters, context, executemany):
        nonlocal writes
        if statement.startswith("UPDATE document_chunks SET lexical_frequencies"):
            writes += 1
            if writes == 501:
                raise RuntimeError("Injected interruption after the first backfill batch")

    event.listen(engine, "before_cursor_execute", interrupt)
    try:
        with pytest.raises(RuntimeError, match="Injected interruption"):
            migrate(engine, "head")
    finally:
        event.remove(engine, "before_cursor_execute", interrupt)
    assert writes == 501
    assert evidence_rows(engine) == before
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0009_attempts"
    migrate(engine, "head")
    assert evidence_rows(engine) == before
    with Session(engine) as db:
        assert db.get(Document, version.document_id).active_version_id == version.id
        chunks = db.scalars(select(Chunk)).all()
        assert len(chunks) == 504
        for chunk in chunks:
            assert chunk.lexical_version == LEXICAL_VERSION
            assert chunk.lexical_frequencies == frequencies(chunk.text)
            assert chunk.lexical_length == sum(frequencies(chunk.text).values())
        assert any(chunk.lexical_length == 0 and chunk.lexical_frequencies == {} for chunk in chunks)
