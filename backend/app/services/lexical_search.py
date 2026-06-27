from __future__ import annotations

import re

from app.core.language import SupportedLanguage


def lexical_score(query: str, content: str, language: SupportedLanguage) -> float:
    query_terms = _terms(query, language)
    content_terms = _terms(content, language)
    if not query_terms or not content_terms:
        return 0.0
    overlap = query_terms & content_terms
    if not overlap:
        return 0.0
    return min(1.0, len(overlap) / len(query_terms))


def _terms(text: str, language: SupportedLanguage) -> set[str]:
    normalized = text.lower().strip()
    if not normalized:
        return set()
    if language == SupportedLanguage.en:
        return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1}
    compact = re.sub(r"\s+", "", normalized)
    if len(compact) <= 2:
        return {compact} if compact else set()
    bigrams = {compact[index : index + 2] for index in range(len(compact) - 1)}
    trigrams = {compact[index : index + 3] for index in range(len(compact) - 2)}
    return bigrams | trigrams
