from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.language import SupportedLanguage


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    metadata: dict[str, int | str]


def estimate_token_count(text: str, language: SupportedLanguage) -> int:
    if language == SupportedLanguage.en:
        return max(1, len(re.findall(r"\w+|[^\w\s]", text)))
    cjk_chars = sum(1 for char in text if not char.isspace())
    return max(1, (cjk_chars + 1) // 2)


def chunk_text(
    text: str,
    language: SupportedLanguage,
    *,
    max_tokens: int = 180,
    overlap_tokens: int = 30,
) -> list[TextChunk]:
    stripped = _collapse_adjacent_duplicate_units(text.strip(), language)
    if not stripped:
        return []
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be non-negative and smaller than max_tokens")

    if language == SupportedLanguage.en:
        return _chunk_english(stripped, max_tokens=max_tokens, overlap_tokens=overlap_tokens)
    return _chunk_cjk(stripped, max_tokens=max_tokens, overlap_tokens=overlap_tokens)


def _chunk_english(text: str, *, max_tokens: int, overlap_tokens: int) -> list[TextChunk]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    chunks: list[TextChunk] = []
    step = max_tokens - overlap_tokens
    start = 0
    while start < len(words):
        end = min(start + max_tokens, len(words))
        content = " ".join(words[start:end])
        chunks.append(
            TextChunk(
                chunk_index=len(chunks),
                content=content,
                token_count=estimate_token_count(content, SupportedLanguage.en),
                metadata={"strategy": "word_window", "start_word": start, "end_word": end},
            )
        )
        if end == len(words):
            break
        start += step
    return chunks


def _chunk_cjk(text: str, *, max_tokens: int, overlap_tokens: int) -> list[TextChunk]:
    max_chars = max_tokens * 2
    overlap_chars = overlap_tokens * 2
    step = max_chars - overlap_chars
    chunks: list[TextChunk] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        content = text[start:end].strip()
        if content:
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    content=content,
                    token_count=estimate_token_count(content, SupportedLanguage.zh),
                    metadata={"strategy": "cjk_char_window", "start_char": start, "end_char": end},
                )
            )
        if end == len(text):
            break
        start += step
    return chunks



def _collapse_adjacent_duplicate_units(text: str, language: SupportedLanguage) -> str:
    if not text:
        return text
    if language == SupportedLanguage.en:
        units = re.findall(r"[^.!?]+[.!?]?|\n+", text)
        separator = " "
    else:
        units = re.findall(r"[^。！？!?]+[。！？!?]?|\n+", text)
        separator = ""
    collapsed: list[str] = []
    previous_normalized = ""
    for unit in units:
        cleaned = unit.strip()
        if not cleaned:
            continue
        normalized = re.sub(r"\s+", "", cleaned).lower()
        if normalized == previous_normalized:
            continue
        collapsed.append(cleaned)
        previous_normalized = normalized
    return separator.join(collapsed)
