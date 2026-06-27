from __future__ import annotations

from dataclasses import dataclass

from app.core.language import SupportedLanguage
from app.services.token_accounting import ModelPricing, estimate_cost, estimate_tokens


@dataclass(frozen=True)
class TokenBudgetPlan:
    allowed: bool
    selected_model: str
    max_retrieved_chunks: int
    use_cache: bool
    compression_required: bool
    route_to_human_review: bool
    estimated_prompt_tokens: int
    estimated_completion_tokens: int
    estimated_total_tokens: int
    estimated_cost: float
    reason: str | None = None


@dataclass(frozen=True)
class ModelCallBudgetPlan:
    allowed: bool
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    max_context_tokens: int
    estimated_cost: float
    compression_required: bool
    route_to_human_review: bool
    reason: str | None = None


class TokenBudgetPlanner:
    def plan(
        self,
        *,
        purpose: str,
        estimated_context_tokens: int,
        requested_completion_tokens: int,
        max_total_tokens: int,
        max_estimated_cost: float,
    ) -> TokenBudgetPlan:
        selected_model = (
            "mock-cheap" if purpose in {"classification", "routing"} else "mock-standard"
        )
        prompt_tokens = max(0, estimated_context_tokens)
        completion_tokens = max(0, requested_completion_tokens)
        total_tokens = prompt_tokens + completion_tokens
        rate = 0.0002 if selected_model == "mock-cheap" else 0.001
        estimated_cost = round((total_tokens / 1000) * rate, 8)
        compression_required = prompt_tokens > int(max_total_tokens * 0.7)
        route_to_review = estimated_cost > max_estimated_cost
        allowed = total_tokens <= max_total_tokens and not route_to_review
        reason = None
        if total_tokens > max_total_tokens:
            reason = "token_budget_exceeded"
        elif route_to_review:
            reason = "cost_budget_exceeded"
        return TokenBudgetPlan(
            allowed=allowed,
            selected_model=selected_model,
            max_retrieved_chunks=max(1, min(8, max_total_tokens // 600)),
            use_cache=True,
            compression_required=compression_required,
            route_to_human_review=route_to_review,
            estimated_prompt_tokens=prompt_tokens,
            estimated_completion_tokens=completion_tokens,
            estimated_total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            reason=reason,
        )

    def plan_model_call(
        self,
        *,
        prompt_text: str,
        completion_text: str,
        language: SupportedLanguage,
        pricing: ModelPricing,
    ) -> ModelCallBudgetPlan:
        prompt_tokens = estimate_tokens(prompt_text, language)
        completion_tokens = estimate_tokens(completion_text, language)
        total_tokens = prompt_tokens + completion_tokens
        estimated = estimate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_token_cost_per_1k=pricing.prompt_token_cost_per_1k,
            completion_token_cost_per_1k=pricing.completion_token_cost_per_1k,
        )
        compression_required = prompt_tokens > int(pricing.max_context_tokens * 0.7)
        allowed = total_tokens <= pricing.max_context_tokens
        return ModelCallBudgetPlan(
            allowed=allowed,
            provider=pricing.provider,
            model=pricing.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            max_context_tokens=pricing.max_context_tokens,
            estimated_cost=estimated,
            compression_required=compression_required,
            route_to_human_review=not allowed,
            reason=None if allowed else "token_budget_exceeded",
        )
