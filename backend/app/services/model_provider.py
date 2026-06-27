from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus, PromptTemplate
from app.services.token_accounting import estimate_cost, estimate_tokens, pricing_for_model


class MockModelProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class MockModelResponse:
    content: str
    ai_run: AIRun


class MockModelProvider:
    provider = "mock"

    def __init__(self, db: Session):
        self.db = db

    def complete(
        self,
        *,
        workspace_id: UUID,
        purpose: str,
        language: SupportedLanguage,
        prompt: str,
        model: str = "mock-standard",
        completion_text: str = "mock response",
        prompt_template: PromptTemplate | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> MockModelResponse:
        started = time.perf_counter()
        pricing = pricing_for_model(model)
        prompt_tokens = estimate_tokens(prompt, language)
        completion_tokens = 0 if fail else estimate_tokens(completion_text, language)
        total_tokens = prompt_tokens + completion_tokens
        estimated = estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_token_cost_per_1k=pricing.prompt_token_cost_per_1k,
            completion_token_cost_per_1k=pricing.completion_token_cost_per_1k,
        )
        ai_run = AIRun(
            workspace_id=workspace_id,
            provider=pricing.provider,
            model=pricing.model,
            purpose=purpose,
            language=language,
            prompt_template_id=prompt_template.id if prompt_template else None,
            prompt_version=prompt_template.version if prompt_template else None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated,
            latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
            cache_hit=cache_hit,
            status=AIRunStatus.failed if fail else AIRunStatus.succeeded,
            error_message="mock provider failure" if fail else None,
        )
        self.db.add(ai_run)
        self.db.commit()
        self.db.refresh(ai_run)
        if fail:
            raise MockModelProviderError("mock provider failure")
        return MockModelResponse(content=completion_text, ai_run=ai_run)
