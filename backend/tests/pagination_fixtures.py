"""Explicit creation order for pagination tests, independent of the host wall clock."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select


def set_creation_order(db, model, workspace_id, names, *, label="name"):
    rows = db.scalars(select(model).where(model.workspace_id == UUID(workspace_id))).all()
    assert len(rows) == len(names)
    for row in rows:
        row.created_at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(
            seconds=names.index(getattr(row, label)))
    db.commit()
