"""Permission-gated original/version changes; caller owns the transaction."""

import hashlib
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select

from app.jobs.models import Job
from app.jobs.queue import authorize, enqueue, request_cancel
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.workspaces.service import membership

MAX_FILE_BYTES = 5 * 1024 * 1024


def admin_scope(db, workspace_id, actor_id):
    authorize(db, workspace_id, actor_id)
    membership(db, workspace_id, actor_id, {"admin"})


def get_document(db, workspace_id, document_id, lock=False):
    query = select(Document).where(Document.workspace_id == workspace_id, Document.id == document_id)
    document = db.scalar(query.with_for_update() if lock else query)
    if document is None:
        raise HTTPException(404, "Document unavailable")
    return document


def decode_upload(filename, original):
    filename = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    if not filename.lower().endswith((".txt", ".md")):
        raise HTTPException(415, "Upload a UTF-8 TXT or Markdown document")
    if len(filename) > 200 or any(ord(character) < 32 for character in filename):
        raise HTTPException(400, "Use a filename of at most 200 characters without control characters")
    if not original or len(original) > MAX_FILE_BYTES:
        raise HTTPException(413, "Document must be between 1 byte and 5 MiB")
    try:
        normalized = original.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as error:
        raise HTTPException(400, "Save the document as UTF-8 text and upload it again") from error
    if not normalized.strip() or "\x00" in normalized:
        raise HTTPException(400, "Document must contain readable text without null characters")
    return filename, normalized


def upload(db, workspace_id, actor_id, filename, original, key, document_id=None):
    admin_scope(db, workspace_id, actor_id)
    filename, normalized = decode_upload(filename, original)
    checksum = hashlib.sha256(original).hexdigest()
    supplied = {
        "document_id": str(document_id) if document_id else None,
        "checksum": checksum,
        "filename": filename,
    }
    existing = db.scalar(select(Job).where(Job.workspace_id == workspace_id, Job.idempotency_key == key))
    if existing:
        if (
            existing.actor_id != actor_id
            or existing.kind != "index_document"
            or any(existing.payload.get(name) != value for name, value in supplied.items())
        ):
            raise HTTPException(409, "This submission key already belongs to different input")
        return db.scalar(
            select(DocumentVersion).where(
                DocumentVersion.workspace_id == workspace_id,
                DocumentVersion.id == uuid.UUID(existing.payload["version_id"]),
            )
        )
    document = get_document(db, workspace_id, document_id, lock=True) if document_id else None
    if document and document.withdrawn:
        raise HTTPException(409, "Restore this withdrawn document before uploading a replacement")
    if document and document.version_number >= 20:
        raise HTTPException(409, "This document has reached its 20-version retention limit")
    retained = db.scalar(
        select(func.coalesce(func.sum(func.octet_length(DocumentVersion.original)), 0)).where(
            DocumentVersion.workspace_id == workspace_id
        )
    )
    if retained + len(original) > 500 * 1024 * 1024:
        raise HTTPException(409, "Workspace original-document storage limit reached")
    if document is None:
        active_count = db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.workspace_id == workspace_id, Document.withdrawn.is_(False))
        )
        if active_count >= 500:
            raise HTTPException(409, "Workspace active-document limit reached")
        document = Document(workspace_id=workspace_id, title=filename)
        db.add(document)
        db.flush()
    if document.desired_version_id:
        previous = db.get(DocumentVersion, document.desired_version_id)
        request_cancel(db, workspace_id, actor_id, previous.job_id)
    version_id = uuid.uuid4()
    job = enqueue(
        db,
        workspace_id,
        actor_id,
        "index_document",
        key,
        {**supplied, "version_id": str(version_id)},
        priority=20,
    )
    document.version_number += 1
    version = DocumentVersion(
        id=version_id,
        workspace_id=workspace_id,
        document_id=document.id,
        job_id=job.id,
        number=document.version_number,
        filename=filename,
        original=original,
        checksum=checksum,
        text=normalized,
    )
    db.add(version)
    db.flush()
    document.desired_version_id = version.id
    return version


def set_withdrawn(db, workspace_id, actor_id, document_id, withdrawn):
    admin_scope(db, workspace_id, actor_id)
    document = get_document(db, workspace_id, document_id, lock=True)
    if not withdrawn and document.withdrawn:
        count = db.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.workspace_id == workspace_id, Document.withdrawn.is_(False))
        )
        if count >= 500:
            raise HTTPException(409, "Workspace active-document limit reached")
    document.withdrawn = withdrawn
    if withdrawn and document.desired_version_id:
        version = db.get(DocumentVersion, document.desired_version_id)
        request_cancel(db, workspace_id, actor_id, version.job_id)
    return document
