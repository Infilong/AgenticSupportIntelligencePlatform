from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.language import SupportedLanguage


@dataclass(frozen=True)
class ModelPricing:
    provider: str
    model: str
    prompt_token_cost_per_1k: float
    completion_token_cost_per_1k: float
    max_context_tokens: int


DEFAULT_MODEL_PRICING = {
    "mock-cheap": ModelPricing("mock", "mock-cheap", 0.0001, 0.0002, 4096),
    "mock-standard": ModelPricing("mock", "mock-standard", 0.0005, 0.001, 8192),
}


def estimate_tokens(text: str, language: SupportedLanguage | None = None) -> int:
    if not text.strip():
        return 0
    if language == SupportedLanguage.ja or language == SupportedLanguage.zh:
        chars = sum(1 for char in text if not char.isspace())
        return max(1, (chars + 1) // 2)
    tokens = re.findall(r"\w+|[^\w\s]", text)
    return max(1, len(tokens))


def estimate_cost(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    prompt_token_cost_per_1k: float,
    completion_token_cost_per_1k: float,
) -> float:
    prompt_cost = (prompt_tokens / 1000) * prompt_token_cost_per_1k
    completion_cost = (completion_tokens / 1000) * completion_token_cost_per_1k
    return round(prompt_cost + completion_cost, 8)


def pricing_for_model(model: str) -> ModelPricing:
    return DEFAULT_MODEL_PRICING.get(model, DEFAULT_MODEL_PRICING["mock-standard"])
