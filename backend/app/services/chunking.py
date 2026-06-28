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
    return _chunk_cjk(
        stripped, language=language, max_tokens=max_tokens, overlap_tokens=overlap_tokens
    )


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


def _chunk_cjk(
    text: str,
    *,
    language: SupportedLanguage,
    max_tokens: int,
    overlap_tokens: int,
) -> list[TextChunk]:
    max_chars = max_tokens * 2
    sentences = _split_cjk_sentences(text)
    chunks: list[TextChunk] = []
    current: list[str] = []
    current_start = 0
    cursor = 0

    for sentence in sentences:
        sentence_start = cursor
        cursor += len(sentence)
        if estimate_token_count(sentence, language) > max_tokens:
            if current:
                _append_cjk_sentence_chunk(
                    chunks,
                    current,
                    language=language,
                    start_char=current_start,
                    end_char=sentence_start,
                )
                current = []
            chunks.extend(
                _chunk_long_cjk_sentence(
                    sentence,
                    language=language,
                    max_chars=max_chars,
                    overlap_tokens=overlap_tokens,
                    base_index=len(chunks),
                    start_offset=sentence_start,
                )
            )
            current_start = cursor
            continue

        candidate = "".join([*current, sentence])
        if current and estimate_token_count(candidate, language) > max_tokens:
            _append_cjk_sentence_chunk(
                chunks,
                current,
                language=language,
                start_char=current_start,
                end_char=sentence_start,
            )
            current = [sentence]
            current_start = sentence_start
        else:
            if not current:
                current_start = sentence_start
            current.append(sentence)

    if current:
        _append_cjk_sentence_chunk(
            chunks, current, language=language, start_char=current_start, end_char=len(text)
        )
    return chunks


def _split_cjk_sentences(text: str) -> list[str]:
    sentences = [
        part.strip()
        for part in re.findall(r"[^。！？!?]+[。！？!?]?", text)
        if part.strip()
    ]
    return sentences or [text]


def _append_cjk_sentence_chunk(
    chunks: list[TextChunk],
    sentences: list[str],
    *,
    language: SupportedLanguage,
    start_char: int,
    end_char: int,
) -> None:
    content = "".join(sentences).strip()
    if not content:
        return
    chunks.append(
        TextChunk(
            chunk_index=len(chunks),
            content=content,
            token_count=estimate_token_count(content, language),
            metadata={
                "strategy": "cjk_sentence_window",
                "start_char": start_char,
                "end_char": end_char,
                "sentence_count": len(sentences),
            },
        )
    )


def _chunk_long_cjk_sentence(
    sentence: str,
    *,
    language: SupportedLanguage,
    max_chars: int,
    overlap_tokens: int,
    base_index: int,
    start_offset: int,
) -> list[TextChunk]:
    overlap_chars = overlap_tokens * 2
    step = max(1, max_chars - overlap_chars)
    chunks: list[TextChunk] = []
    start = 0
    while start < len(sentence):
        end = min(start + max_chars, len(sentence))
        content = sentence[start:end].strip()
        if content:
            absolute_start = start_offset + start
            absolute_end = start_offset + end
            chunks.append(
                TextChunk(
                    chunk_index=base_index + len(chunks),
                    content=content,
                    token_count=estimate_token_count(content, language),
                    metadata={
                        "strategy": "cjk_long_sentence_window",
                        "start_char": absolute_start,
                        "end_char": absolute_end,
                    },
                )
            )
        if end == len(sentence):
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
