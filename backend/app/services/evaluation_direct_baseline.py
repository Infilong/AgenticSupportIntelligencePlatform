"""Configured direct baseline with shared budget admission."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.services.budgeted_model_provider import BudgetedModelProvider
from app.services.model_provider import ModelProviderResponse


def run_direct_baseline(db: Session, *, workspace_id: UUID, evaluation_run_id: UUID,
                        question: str, language: SupportedLanguage) -> ModelProviderResponse:
    mock_answer = {
        "ja": "返金についてはサポートに確認してください。",
        "zh": "请联系支持团队确认退款政策。",
        "en": "Please contact support to confirm the refund policy.",
    }[str(language)]
    return BudgetedModelProvider(db).complete(
        workspace_id=workspace_id, evaluation_run_id=evaluation_run_id,
        purpose="evaluation_direct_llm", language=language, prompt=question,
        model="mock-standard", completion_text=mock_answer,
    )
