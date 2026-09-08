from typing import Annotated
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, select

from app.jobs.models import Job
from app.modules.identity.dependencies import CurrentUser, Database
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.knowledge.schemas import (
    DocumentDetail,
    DocumentPage,
    SourcePreview,
    UploadResult,
    Withdrawal,
)
from app.modules.knowledge.service import MAX_FILE_BYTES, get_document, set_withdrawn, upload
from app.modules.workspaces.service import membership

router = APIRouter(prefix="/api/workspaces/{workspace_id}/documents", tags=["knowledge"])


def summary_query():
    return (
        select(Document, Job.state, Job.error_code)
        .outerjoin(DocumentVersion, DocumentVersion.id == Document.desired_version_id)
        .outerjoin(Job, Job.id == DocumentVersion.job_id)
    )


def summary(row):
    document, state, error = row
    return {
        "id": document.id,
        "title": document.title,
        "withdrawn": document.withdrawn,
        "active_version_id": document.active_version_id,
        "desired_version_id": document.desired_version_id,
        "version_number": document.version_number,
        "job_status": state,
        "error_code": error,
    }


@router.get("", response_model=DocumentPage)
def list_documents(
    workspace_id: UUID,
    user: CurrentUser,
    db: Database,
    search: str = Query("", max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=50),
):
    membership(db, workspace_id, user.id)
    filters = [Document.workspace_id == workspace_id, Document.title.icontains(search, autoescape=True)]
    total = db.scalar(select(func.count()).select_from(Document).where(*filters))
    rows = db.execute(
        summary_query()
        .where(*filters)
        .order_by(Document.created_at.desc(), Document.id)
        .offset(offset)
        .limit(limit)
    )
    return {"items": [summary(row) for row in rows], "total": total}


@router.post("", response_model=UploadResult, status_code=202)
def upload_document(
    workspace_id: UUID,
    user: CurrentUser,
    db: Database,
    key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=100)],
    file: UploadFile = File(...),
    document_id: UUID | None = Form(None),
):
    original = file.file.read(MAX_FILE_BYTES + 1)
    version = upload(db, workspace_id, user.id, file.filename, original, key, document_id)
    db.commit()
    return {"document_id": version.document_id, "version_id": version.id, "job_id": version.job_id}


@router.get("/{document_id}", response_model=DocumentDetail)
def document_detail(workspace_id: UUID, document_id: UUID, user: CurrentUser, db: Database):
    membership(db, workspace_id, user.id)
    get_document(db, workspace_id, document_id)
    row = db.execute(
        summary_query().where(Document.workspace_id == workspace_id, Document.id == document_id)
    ).one()
    versions = db.execute(
        select(DocumentVersion, Job.state, Job.error_code)
        .join(Job, Job.id == DocumentVersion.job_id)
        .where(DocumentVersion.workspace_id == workspace_id, DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.number.desc())
        .limit(20)
    )
    return {
        "document": summary(row),
        "versions": [
            {
                "id": version.id,
                "number": version.number,
                "filename": version.filename,
                "checksum": version.checksum,
                "indexed_at": version.indexed_at,
                "job_status": state,
                "error_code": error,
            }
            for version, state, error in versions
        ],
    }


@router.patch("/{document_id}", status_code=204)
def withdraw_document(
    workspace_id: UUID, document_id: UUID, body: Withdrawal, user: CurrentUser, db: Database
):
    set_withdrawn(db, workspace_id, user.id, document_id, body.withdrawn)
    db.commit()


def read_version(db, workspace_id, document_id, version_id, actor_id):
    membership(db, workspace_id, actor_id)
    document = get_document(db, workspace_id, document_id)
    version = db.scalar(
        select(DocumentVersion).where(
            DocumentVersion.workspace_id == workspace_id,
            DocumentVersion.document_id == document_id,
            DocumentVersion.id == version_id,
        )
    )
    if version is None:
        raise HTTPException(404, "Document version unavailable")
    return document, version


@router.get("/{document_id}/versions/{version_id}", response_model=SourcePreview)
def preview(
    workspace_id: UUID,
    document_id: UUID,
    version_id: UUID,
    user: CurrentUser,
    db: Database,
    offset: int = Query(0, ge=0),
    limit: int = Query(4000, ge=1, le=12000),
):
    document, version = read_version(db, workspace_id, document_id, version_id, user.id)
    return {
        "version_id": version.id,
        "text": version.text[offset : offset + limit],
        "offset": offset,
        "total_characters": len(version.text),
        "checksum": version.checksum,
        "active": document.active_version_id == version.id,
        "withdrawn": document.withdrawn,
    }


@router.get("/{document_id}/versions/{version_id}/original")
def original(workspace_id: UUID, document_id: UUID, version_id: UUID, user: CurrentUser, db: Database):
    _, version = read_version(db, workspace_id, document_id, version_id, user.id)
    return Response(
        version.original,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(version.filename)}"},
    )
