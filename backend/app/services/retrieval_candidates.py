"""Permission-scoped candidate SQL and PostgreSQL nearest-neighbor ranking."""

from sqlalchemy import Float, and_, bindparam, func, or_, select

from app.models.knowledge import (
    DocumentChunk,
    DocumentStatus,
    DocumentVersion,
    Embedding,
    EmbeddingVector,
    KnowledgeDocument,
)
from app.services.retrieval_embeddings import RetrievalError, embed_query


def candidate_statement(*, workspace_id, language, document_id,
                        allowed_document_ids, strategy, provider):
    latest_versions = (
        select(
            DocumentVersion.knowledge_document_id.label("document_id"),
            func.max(DocumentVersion.version).label("version"),
        )
        .where(DocumentVersion.workspace_id == workspace_id)
        .group_by(DocumentVersion.knowledge_document_id)
        .subquery()
    )
    statement = (
        select(DocumentChunk, Embedding, DocumentVersion, KnowledgeDocument)
        .join(Embedding, Embedding.document_chunk_id == DocumentChunk.id)
        .join(DocumentVersion, DocumentVersion.id == DocumentChunk.document_version_id)
        .join(KnowledgeDocument, KnowledgeDocument.id == DocumentVersion.knowledge_document_id)
        .join(latest_versions, and_(
            latest_versions.c.document_id == KnowledgeDocument.id,
            latest_versions.c.version == DocumentVersion.version,
        ))
        .where(
            DocumentChunk.workspace_id == workspace_id,
            Embedding.workspace_id == workspace_id,
            DocumentVersion.workspace_id == workspace_id,
            KnowledgeDocument.workspace_id == workspace_id,
            KnowledgeDocument.status == DocumentStatus.indexed,
            DocumentChunk.language == language,
        )
    )
    if document_id is not None:
        statement = statement.where(KnowledgeDocument.id == document_id)
    if allowed_document_ids is not None:
        statement = statement.where(KnowledgeDocument.id.in_(allowed_document_ids))
    if strategy != "lexical":
        statement = statement.where(
            Embedding.provider == provider.provider,
            Embedding.model == provider.model,
        )
    return statement


def postgres_candidates(db, statement, provider, query, limit):
    # Validate in SQL without transferring every stored vector to the application.
    invalid = statement.with_only_columns(Embedding.id).where(or_(
        func.vector_dims(Embedding.vector) != provider.dimensions,
        func.vector_norm(Embedding.vector) == 0,
    )).limit(1)
    if db.execute(invalid).first():
        raise RetrievalError("Invalid stored embedding dimensions or zero magnitude")
    if not db.execute(statement.with_only_columns(Embedding.id).limit(1)).first():
        return [], []
    vector = embed_query(provider, query, [])
    distance = Embedding.vector.op("<=>", return_type=Float)(
        bindparam("query_vector", value=vector, type_=EmbeddingVector()))
    ranked = statement.add_columns(distance.label("distance")).order_by(
        distance, DocumentChunk.id).limit(limit)
    return db.execute(ranked).all(), vector
