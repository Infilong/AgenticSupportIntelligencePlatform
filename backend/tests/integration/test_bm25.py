import math
import uuid

import pytest
from sqlalchemy import func, null, select, update
from sqlalchemy.orm import Session

from app.modules.knowledge.bm25 import LexicalIndexIncomplete, candidates
from app.modules.knowledge.ingestion import SPACE
from app.modules.knowledge.lexical import LEXICAL_VERSION, frequencies
from app.modules.knowledge.models import Chunk, Document
from app.modules.knowledge.retrieval import access
from tests.integration.test_knowledge import add_version


def seed_chunks(system, texts, *, workspace=None, withdrawn=False, space=SPACE):
    version = add_version(system)
    workspace = workspace or system["workspace"]
    with Session(system["engine"]) as db, db.begin():
        document = db.get(Document, version.document_id)
        if workspace != system["workspace"]:
            # Use a genuine foreign document/version rather than forge composite references.
            from app.modules.knowledge.service import upload

            version = upload(
                db, workspace, system["users"]["other"].id, "foreign.txt", b"foreign", uuid.uuid4().hex, None
            )
            db.flush()
            document = db.get(Document, version.document_id)
        document.active_version_id = version.id
        document.withdrawn = withdrawn
        ids = []
        for index, text in enumerate(texts):
            chunk = Chunk(
                workspace_id=workspace,
                version_id=version.id,
                ordinal=index,
                text=text,
                start_offset=0,
                end_offset=len(text),
                section="Synthetic",
                token_count=len(text),
                embedding=[1.0] + [0.0] * 383,
                embedding_space=space,
                lexical_terms=sorted(frequencies(text)),
            )
            db.add(chunk)
            db.flush()
            ids.append(str(chunk.id))
        return ids, version.document_id


def search(system, query):
    with Session(system["engine"]) as db, db.begin():
        access(db, system["workspace"], system["users"]["viewer"].id)
        return candidates(db, system["workspace"], query)


def test_bm25_formula_tf_length_and_scoped_statistics(system):
    texts = ["refund", "refund refund", "refund policy policy policy", "unrelated policy", "！"]
    ids, _ = seed_chunks(system, texts)
    expected = {}
    for index in range(3):
        tf, dl = (1, 1) if index == 0 else (2, 2) if index == 1 else (1, 4)
        expected[ids[index]] = (
            math.log(1 + (5 - 3 + 0.5) / (3 + 0.5)) * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * dl / (9 / 5)))
        )
    actual = search(system, "refund")
    assert {row["chunk_id"]: row["bm25_score"] for row in actual} == pytest.approx(expected)
    assert actual[0]["chunk_id"] == ids[1]
    assert actual[-1]["chunk_id"] == ids[2]
    assert search(system, "refund refund") == actual
    seed_chunks(system, ["refund " * 100], workspace=system["foreign"])
    seed_chunks(system, ["refund " * 100], withdrawn=True)
    seed_chunks(system, ["refund " * 100], space="incompatible-space")
    stale_ids, stale_doc = seed_chunks(system, ["refund " * 100])
    with Session(system["engine"]) as db, db.begin():
        db.get(Document, stale_doc).active_version_id = None
    assert search(system, "refund") == actual
    assert stale_ids[0] not in [row["chunk_id"] for row in actual]


def test_bm25_empty_unicode_ties_and_missing_metadata(system):
    assert search(system, "refund") == []
    ids, _ = seed_chunks(system, ["ERROR-8422 政策", "ＥＲＲＯＲ－８４２２ 政策"])
    rows = search(system, "error-8422 政策")
    assert [row["chunk_id"] for row in rows] == sorted(ids)
    assert rows[0]["bm25_score"] == pytest.approx(rows[1]["bm25_score"])
    assert search(system, "！！！") == []
    with Session(system["engine"]) as db, db.begin():
        db.execute(update(Chunk).where(Chunk.id == uuid.UUID(ids[0])).values(lexical_version=None))
    with pytest.raises(LexicalIndexIncomplete):
        search(system, "refund")

    with Session(system["engine"]) as db, db.begin():
        db.execute(
            update(Chunk)
            .where(Chunk.id == uuid.UUID(ids[0]))
            .values(lexical_version=LEXICAL_VERSION, lexical_frequencies=null())
        )
    with pytest.raises(LexicalIndexIncomplete):
        search(system, "refund")
    with Session(system["engine"]) as db, db.begin():
        chunk = db.get(Chunk, uuid.UUID(ids[0]))
        chunk.lexical_frequencies = frequencies(chunk.text)
    with Session(system["engine"]) as db, db.begin():
        chunk = db.get(Chunk, uuid.UUID(ids[0]))
        chunk.lexical_version = LEXICAL_VERSION
        chunk.lexical_frequencies = None  # SQLAlchemy persists JSON null, not SQL NULL.
    with Session(system["engine"]) as db:
        assert (
            db.scalar(
                select(func.jsonb_typeof(Chunk.lexical_frequencies)).where(Chunk.id == uuid.UUID(ids[0]))
            )
            == "null"
        )
    with pytest.raises(LexicalIndexIncomplete):
        search(system, "refund")


def test_new_chunk_defaults_store_actual_frequency_and_length(system):
    ids, _ = seed_chunks(system, ["policy policy policy"])
    with Session(system["engine"]) as db:
        chunk = db.scalar(select(Chunk).where(Chunk.id == uuid.UUID(ids[0])))
        assert chunk.lexical_frequencies == {"policy": 3}
        assert chunk.lexical_length == 3
