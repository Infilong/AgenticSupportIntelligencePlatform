"""Bounded, atomic customer-data admission; never ingestion into trusted knowledge."""

import hashlib
import json
import uuid

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select

from app.jobs.queue import authorize
from app.modules.conversations.models import MessageImport
from app.modules.conversations.schemas import ImportRow
from app.modules.support.context import digest
from app.modules.support.models import Message, SupportRun
from app.modules.support.service import initial_run
from app.modules.workspaces.service import membership

MAX_BYTES, MAX_ROWS = 1024 * 1024, 100


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def parse(original):
    if len(original) > MAX_BYTES:
        raise HTTPException(413, "Import exceeds 1 MiB")
    try:
        text = original.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "Use a UTF-8 JSONL file") from None
    rows = []
    for number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        if len(rows) >= MAX_ROWS:
            raise HTTPException(422, "Import supports at most 100 messages")
        try:
            rows.append(ImportRow.model_validate(json.loads(line, object_pairs_hook=unique_object)))
        except (ValueError, ValidationError, RecursionError):
            raise HTTPException(
                422,
                f"Line {number}: use original (1–1000 characters), language (en/ja/zh), "
                "and optional labels (up to 10, 32 characters each); no duplicate or extra fields",
            ) from None
    if not rows:
        raise HTTPException(422, "The file contains no messages")
    return rows


def import_messages(db, workspace_id, actor_id, filename, original, key):
    authorize(db, workspace_id, actor_id)
    if (
        not filename
        or not filename.lower().endswith(".jsonl")
        or len(filename) > 160
        or any(ord(c) < 32 for c in filename)
    ):
        raise HTTPException(422, "Choose a .jsonl filename of at most 160 characters")
    rows = parse(original)
    value = digest(
        {"actor": str(actor_id), "filename": filename, "sha256": hashlib.sha256(original).hexdigest()}
    )
    previous = db.scalar(
        select(MessageImport).where(
            MessageImport.workspace_id == workspace_id, MessageImport.submission_key == key
        )
    )
    if previous:
        if previous.input_hash != value:
            raise HTTPException(409, "Import key already belongs to different input")
        return previous
    count = db.scalar(select(func.count()).select_from(Message).where(Message.workspace_id == workspace_id))
    if count + len(rows) > 50000:
        raise HTTPException(409, "Import would exceed the 50000-message workspace limit")
    batch = MessageImport(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        actor_id=actor_id,
        filename=filename,
        submission_key=key,
        input_hash=value,
        message_count=len(rows),
    )
    db.add(batch)
    db.flush()
    for number, row in enumerate(rows, 1):
        db.add(
            Message(
                workspace_id=workspace_id,
                actor_id=actor_id,
                original=row.original,
                language=row.language,
                labels=row.labels,
                import_id=batch.id,
                submission_key=f"import:{batch.id}:{number}",
                input_hash=digest(row.model_dump()),
            )
        )
    db.flush()
    return batch


def get_message(db, workspace_id, message_id):
    message = db.scalar(select(Message).where(Message.workspace_id == workspace_id, Message.id == message_id))
    if message is None:
        raise HTTPException(404, "Message not found")
    return message


def detail(db, workspace_id, actor_id, message_id):
    membership(db, workspace_id, actor_id)
    message = get_message(db, workspace_id, message_id)
    batch = (
        db.scalar(
            select(MessageImport).where(
                MessageImport.workspace_id == workspace_id, MessageImport.id == message.import_id
            )
        )
        if message.import_id
        else None
    )
    run_id = db.scalar(
        select(SupportRun.id)
        .where(SupportRun.workspace_id == workspace_id, SupportRun.message_id == message_id)
        .order_by(SupportRun.attempt_number.desc())
        .limit(1)
    )
    return {
        "id": message.id,
        "original": message.original,
        "language": message.language,
        "labels": message.labels,
        "created_at": message.created_at,
        "import_filename": batch.filename if batch else None,
        "latest_run_id": run_id,
    }


def start(db, workspace_id, actor_id, message_id):
    authorize(db, workspace_id, actor_id)
    message = get_message(db, workspace_id, message_id)
    membership(db, workspace_id, message.actor_id, {"operator", "admin"})
    run = db.scalar(
        select(SupportRun)
        .where(SupportRun.workspace_id == workspace_id, SupportRun.message_id == message_id)
        .order_by(SupportRun.attempt_number)
        .limit(1)
    )
    if run is None:
        run = initial_run(db, message, actor_id)
    return {"message_id": message.id, "run_id": run.id, "job_id": run.job_id}
