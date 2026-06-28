from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.language import SupportedLanguage
from app.models.ai import AIRun, AIRunStatus, PromptTemplate
from app.services.model_config_service import ModelConfigService
from app.services.token_accounting import ModelPricing, estimate_cost, estimate_tokens


class ModelProviderError(RuntimeError):
    def __init__(self, message: str, *, ai_run: AIRun | None = None):
        super().__init__(message)
        self.ai_run = ai_run


class MockModelProviderError(ModelProviderError):
    pass


@dataclass(frozen=True)
class ModelProviderResponse:
    content: str
    ai_run: AIRun


MockModelResponse = ModelProviderResponse


class ModelProvider(Protocol):
    def complete(
        self,
        *,
        workspace_id: UUID,
        purpose: str,
        language: SupportedLanguage,
        prompt: str,
        model: str = "mock-standard",
        model_config_id: UUID | None = None,
        completion_text: str = "mock response",
        prompt_template: PromptTemplate | None = None,
        graph_run_id: UUID | None = None,
        graph_step_id: UUID | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> ModelProviderResponse: ...


class OpenAIChatTransport(Protocol):
    def create_chat_completion(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        timeout_seconds: int,
    ) -> dict[str, Any]: ...


class UrllibOpenAIChatTransport:
    def create_chat_completion(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        url = f"{base_url.rstrip('/')}/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


class ConfiguredModelProvider:
    def __init__(self, db: Session, openai_provider: OpenAICompatibleModelProvider | None = None):
        self.db = db
        self.openai_provider = openai_provider or OpenAICompatibleModelProvider(db)
        self.mock_provider = MockModelProvider(db)

    def complete(self, **kwargs: Any) -> ModelProviderResponse:
        pricing = ModelConfigService(self.db).resolve_pricing(
            workspace_id=kwargs["workspace_id"],
            purpose=kwargs["purpose"],
            fallback_model=kwargs.get("model", "mock-standard"),
            model_config_id=kwargs.get("model_config_id"),
        )
        if pricing.provider.strip().lower() in {"openai", "openai-compatible"}:
            return self.openai_provider.complete_with_pricing(pricing=pricing, **kwargs)
        return self.mock_provider.complete(**kwargs)


class OpenAICompatibleModelProvider:
    provider = "openai"

    def __init__(
        self,
        db: Session,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        transport: OpenAIChatTransport | None = None,
    ):
        self.db = db
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.timeout_seconds = timeout_seconds or settings.openai_timeout_seconds
        self.transport = transport or UrllibOpenAIChatTransport()

    def complete(
        self,
        *,
        workspace_id: UUID,
        purpose: str,
        language: SupportedLanguage,
        prompt: str,
        model: str = "mock-standard",
        model_config_id: UUID | None = None,
        completion_text: str = "mock response",
        prompt_template: PromptTemplate | None = None,
        graph_run_id: UUID | None = None,
        graph_step_id: UUID | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> ModelProviderResponse:
        pricing = ModelConfigService(self.db).resolve_pricing(
            workspace_id=workspace_id,
            purpose=purpose,
            fallback_model=model,
            model_config_id=model_config_id,
        )
        return self.complete_with_pricing(
            pricing=pricing,
            workspace_id=workspace_id,
            purpose=purpose,
            language=language,
            prompt=prompt,
            model=model,
            completion_text=completion_text,
            prompt_template=prompt_template,
            graph_run_id=graph_run_id,
            graph_step_id=graph_step_id,
            cache_hit=cache_hit,
            fail=fail,
        )

    def complete_with_pricing(
        self,
        *,
        pricing: ModelPricing,
        workspace_id: UUID,
        purpose: str,
        language: SupportedLanguage,
        prompt: str,
        model: str = "mock-standard",
        model_config_id: UUID | None = None,
        completion_text: str = "mock response",
        prompt_template: PromptTemplate | None = None,
        graph_run_id: UUID | None = None,
        graph_step_id: UUID | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> ModelProviderResponse:
        started = time.perf_counter()
        prompt_tokens = estimate_tokens(prompt, language)
        if fail:
            ai_run = _record_ai_run(
                self.db,
                workspace_id=workspace_id,
                graph_run_id=graph_run_id,
                graph_step_id=graph_step_id,
                provider=pricing.provider,
                model=pricing.model,
                purpose=purpose,
                language=language,
                prompt_template=prompt_template,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                estimated_cost=0.0,
                latency_ms=_latency_ms(started),
                cache_hit=cache_hit,
                status=AIRunStatus.failed,
                error_message="model provider forced failure",
            )
            raise ModelProviderError("model provider forced failure", ai_run=ai_run)
        if not self.api_key:
            message = (
                "openai_api_key_missing: set OPENAI_API_KEY before activating "
                "an OpenAI provider"
            )
            ai_run = _record_ai_run(
                self.db,
                workspace_id=workspace_id,
                graph_run_id=graph_run_id,
                graph_step_id=graph_step_id,
                provider=pricing.provider,
                model=pricing.model,
                purpose=purpose,
                language=language,
                prompt_template=prompt_template,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                estimated_cost=0.0,
                latency_ms=_latency_ms(started),
                cache_hit=cache_hit,
                status=AIRunStatus.failed,
                error_message=message,
            )
            raise ModelProviderError(message, ai_run=ai_run)
        try:
            payload = self.transport.create_chat_completion(
                api_key=self.api_key,
                base_url=self.base_url,
                model=pricing.model,
                prompt=prompt,
                timeout_seconds=self.timeout_seconds,
            )
            content = _extract_chat_content(payload)
            usage = payload.get("usage") if isinstance(payload, dict) else None
            if isinstance(usage, dict):
                prompt_tokens = int(usage.get("prompt_tokens") or prompt_tokens)
                completion_tokens = int(
                    usage.get("completion_tokens") or estimate_tokens(content, language)
                )
            else:
                completion_tokens = estimate_tokens(content, language)
            estimated = estimate_cost(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                prompt_token_cost_per_1k=pricing.prompt_token_cost_per_1k,
                completion_token_cost_per_1k=pricing.completion_token_cost_per_1k,
            )
            ai_run = _record_ai_run(
                self.db,
                workspace_id=workspace_id,
                graph_run_id=graph_run_id,
                graph_step_id=graph_step_id,
                provider=pricing.provider,
                model=pricing.model,
                purpose=purpose,
                language=language,
                prompt_template=prompt_template,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                estimated_cost=estimated,
                latency_ms=_latency_ms(started),
                cache_hit=cache_hit,
                status=AIRunStatus.succeeded,
                error_message=None,
            )
            return ModelProviderResponse(content=content, ai_run=ai_run)
        except (OSError, urllib.error.URLError, ValueError, KeyError, TypeError) as exc:
            message = f"openai_provider_error: {exc}"
            ai_run = _record_ai_run(
                self.db,
                workspace_id=workspace_id,
                graph_run_id=graph_run_id,
                graph_step_id=graph_step_id,
                provider=pricing.provider,
                model=pricing.model,
                purpose=purpose,
                language=language,
                prompt_template=prompt_template,
                prompt_tokens=prompt_tokens,
                completion_tokens=0,
                estimated_cost=0.0,
                latency_ms=_latency_ms(started),
                cache_hit=cache_hit,
                status=AIRunStatus.failed,
                error_message=message,
            )
            raise ModelProviderError(message, ai_run=ai_run) from exc


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
        model_config_id: UUID | None = None,
        completion_text: str = "mock response",
        prompt_template: PromptTemplate | None = None,
        graph_run_id: UUID | None = None,
        graph_step_id: UUID | None = None,
        cache_hit: bool = False,
        fail: bool = False,
    ) -> ModelProviderResponse:
        started = time.perf_counter()
        pricing = ModelConfigService(self.db).resolve_pricing(
            workspace_id=workspace_id,
            purpose=purpose,
            fallback_model=model,
            model_config_id=model_config_id,
        )
        prompt_tokens = estimate_tokens(prompt, language)
        requested_completion_tokens = 0 if fail else estimate_tokens(completion_text, language)
        requested_total_tokens = prompt_tokens + requested_completion_tokens
        context_exceeded = requested_total_tokens > pricing.max_context_tokens
        completion_tokens = 0 if fail or context_exceeded else requested_completion_tokens
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
        ai_run = _record_ai_run(
            self.db,
            workspace_id=workspace_id,
            graph_run_id=graph_run_id,
            graph_step_id=graph_step_id,
            provider=pricing.provider,
            model=pricing.model,
            purpose=purpose,
            language=language,
            prompt_template=prompt_template,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            estimated_cost=estimated,
            latency_ms=_latency_ms(started),
            cache_hit=cache_hit,
            status=AIRunStatus.failed if fail or context_exceeded else AIRunStatus.succeeded,
            error_message=error_message,
        )
        if context_exceeded:
            raise MockModelProviderError(error_message or "model context exceeded", ai_run=ai_run)
        if fail:
            raise MockModelProviderError("mock provider failure", ai_run=ai_run)
        return ModelProviderResponse(content=completion_text, ai_run=ai_run)


def _extract_chat_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenAI response did not include choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("OpenAI response choice was invalid")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("OpenAI response choice did not include a message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenAI response message content was empty")
    return content.strip()


def _record_ai_run(
    db: Session,
    *,
    workspace_id: UUID,
    graph_run_id: UUID | None,
    graph_step_id: UUID | None,
    provider: str,
    model: str,
    purpose: str,
    language: SupportedLanguage,
    prompt_template: PromptTemplate | None,
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
        provider=provider,
        model=model,
        purpose=purpose,
        language=language,
        prompt_template_id=prompt_template.id if prompt_template else None,
        prompt_version=prompt_template.version if prompt_template else None,
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


def _latency_ms(started: float) -> int:
    return max(1, int((time.perf_counter() - started) * 1000))
