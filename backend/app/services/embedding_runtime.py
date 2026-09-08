"""Provider selection after authorization; both indexing and queries use these settings."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.language import SupportedLanguage
from app.services.accounted_embeddings import AccountedEmbeddingProvider
from app.services.embedding_api import EmbeddingAPI
from app.services.embedding_attempts import EmbeddingAttemptLedger
from app.services.embedding_provider import EmbeddingProvider, MockEmbeddingProvider


def configured_embedding_provider(db: Session, *, workspace_id: UUID,
                                  language: SupportedLanguage, purpose: str,
                                  graph_run_id: UUID | None = None) -> EmbeddingProvider:
    settings = get_settings()
    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider()
    return AccountedEmbeddingProvider(
        api=EmbeddingAPI(api_key=settings.openai_api_key, model=settings.embedding_model,
                         dimensions=settings.embedding_dimensions,
                         timeout_seconds=settings.openai_timeout_seconds),
        ledger=EmbeddingAttemptLedger(db.get_bind().engine), workspace_id=workspace_id,
        language=language, token_cost_per_1k=settings.embedding_token_cost_per_1k, purpose=purpose,
        graph_run_id=graph_run_id,
    )
