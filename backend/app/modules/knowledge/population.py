"""One active, authorized-workspace source population for retrieval and its statistics."""

from sqlalchemy import select

from app.modules.knowledge.models import Chunk, Document, DocumentVersion
from app.providers.local_models import SPACE


def active_chunks(workspace_id):
    # Caller must first authorize the actor and hold the shared workspace lock.
    return (
        select(Chunk)
        .join(
            Document,
            (Document.active_version_id == Chunk.version_id) & (Document.workspace_id == Chunk.workspace_id),
        )
        .join(
            DocumentVersion,
            (DocumentVersion.id == Chunk.version_id) & (DocumentVersion.workspace_id == Chunk.workspace_id),
        )
        .where(
            Chunk.workspace_id == workspace_id, Document.withdrawn.is_(False), Chunk.embedding_space == SPACE
        )
    )
