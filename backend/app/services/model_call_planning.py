from __future__ import annotations

from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import PromptTemplate
from app.services.model_config_service import ModelConfigService
from app.services.support_prompts import build_draft_response_prompt
from app.services.token_budget import ModelCallBudgetPlan, TokenBudgetPlanner


def plan_model_call(
    *,
    db: Session,
    workspace_id: UUID,
    purpose: str,
    fallback_model: str,
    prompt_text: str,
    completion_text: str,
    language: SupportedLanguage,
    model_config_id: UUID | None = None,
) -> ModelCallBudgetPlan:
    pricing = ModelConfigService(db).resolve_pricing(
        workspace_id=workspace_id,
        purpose=purpose,
        fallback_model=fallback_model,
        model_config_id=model_config_id,
    )
    return TokenBudgetPlanner().plan_model_call(
        prompt_text=prompt_text,
        completion_text=completion_text,
        language=language,
        pricing=pricing,
    )


def fit_draft_documents_to_budget(
    *,
    db: Session,
    workspace_id: UUID,
    input_message: str,
    language: SupportedLanguage,
    documents: list[Document],
    completion_text: str,
    prompt_template: PromptTemplate,
    model_config_id: UUID | None = None,
) -> tuple[list[Document], ModelCallBudgetPlan, int]:
    current_documents = list(documents)
    trimmed_count = 0
    while True:
        prompt_text = build_draft_response_prompt(
            input_message=input_message,
            language=language,
            documents=current_documents,
            prompt_template=prompt_template,
        )
        plan = plan_model_call(
            db=db,
            workspace_id=workspace_id,
            purpose="draft_response",
            fallback_model="mock-standard",
            prompt_text=prompt_text,
            completion_text=completion_text,
            language=language,
            model_config_id=model_config_id,
        )
        if plan.allowed or not current_documents:
            return current_documents, plan, trimmed_count
        current_documents = current_documents[:-1]
        trimmed_count += 1
