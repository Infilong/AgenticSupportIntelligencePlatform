from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus, PromptTemplate
from app.services.model_config_service import ModelConfigService
from app.services.token_accounting import estimate_cost, estimate_tokens


class MockModelProviderError(RuntimeError):
    def __init__(self, message: str, *, ai_run: AIRun | None = None):
        super().__init__(message)
        self.ai_run = ai_run


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
        graph_run_id: UUID | None = None,
        graph_step_id: UUID | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> MockModelResponse:
        started = time.perf_counter()
        pricing = ModelConfigService(self.db).resolve_pricing(
            workspace_id=workspace_id, purpose=purpose, fallback_model=model
        )
        prompt_tokens = estimate_tokens(prompt, language)
        requested_completion_tokens = 0 if fail else estimate_tokens(completion_text, language)
        requested_total_tokens = prompt_tokens + requested_completion_tokens
        context_exceeded = requested_total_tokens > pricing.max_context_tokens
        completion_tokens = 0 if fail or context_exceeded else requested_completion_tokens
        total_tokens = prompt_tokens + completion_tokens
        estimated = 0.0 if context_exceeded else estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_token_cost_per_1k=pricing.prompt_token_cost_per_1k,
            completion_token_cost_per_1k=pricing.completion_token_cost_per_1k,
        )
        error_message = None
        if context_exceeded:
            error_message = (
                f"model_context_exceeded: requested {requested_total_tokens} tokens "
                f"but {pricing.model} allows {pricing.max_context_tokens}"
            )
        elif fail:
            error_message = "mock provider failure"
        ai_run = AIRun(
            workspace_id=workspace_id,
            graph_run_id=graph_run_id,
            graph_step_id=graph_step_id,
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
            status=AIRunStatus.failed if fail or context_exceeded else AIRunStatus.succeeded,
            error_message=error_message,
        )
        self.db.add(ai_run)
        self.db.commit()
        self.db.refresh(ai_run)
        if context_exceeded:
            raise MockModelProviderError(error_message or "model context exceeded", ai_run=ai_run)
        if fail:
            raise MockModelProviderError("mock provider failure", ai_run=ai_run)
        return MockModelResponse(content=completion_text, ai_run=ai_run)
