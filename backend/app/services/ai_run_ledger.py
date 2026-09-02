from __future__ import annotations

import hashlib
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus, PromptTemplate


def record_ai_run(
    db: Session,
    *,
    workspace_id: UUID,
    graph_run_id: UUID | None,
    graph_step_id: UUID | None,
    provider: str,
    model: str,
    model_config_id: UUID | None,
    purpose: str,
    language: SupportedLanguage,
    prompt_template: PromptTemplate | None,
    prompt: str,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost: float,
    latency_ms: int,
    cache_hit: bool,
    status: AIRunStatus,
    error_message: str | None,
) -> AIRun:
    ai_run = AIRun(
        workspace_id=workspace_id,
        graph_run_id=graph_run_id,
        graph_step_id=graph_step_id,
        model_config_id=model_config_id,
        provider=provider,
        model=model,
        purpose=purpose,
        language=language,
        prompt_template_id=prompt_template.id if prompt_template else None,
        prompt_version=prompt_template.version if prompt_template else None,
        rendered_prompt_hash=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        estimated_cost=estimated_cost,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        status=status,
        error_message=error_message,
    )
    db.add(ai_run)
    db.commit()
    db.refresh(ai_run)
    return ai_run
