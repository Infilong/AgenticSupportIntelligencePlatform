"""Normalized-text character offsets, model-token bounds and multilingual lexical terms."""

import re
from dataclasses import dataclass

from app.modules.knowledge.span_splitter import SpanSplitter


@dataclass(frozen=True)
class Passage:
    text: str
    start: int
    end: int
    section: str
    token_count: int


def lexical_terms(text):
    terms = set(re.findall(r"[a-z0-9][a-z0-9_-]+", text.casefold()))
    for run in re.findall(r"[\u3040-\u30ff\u3400-\u9fff]+", text):
        terms.update(run[index : index + 2] for index in range(max(1, len(run) - 1)))
    return sorted(terms)


def source_blocks(text):
    headings = list(re.finditer(r"(?m)^#{1,6}\s+(.+)$", text))
    boundaries = [(0, "Document")]
    for heading in headings:
        if heading.start() == 0:
            boundaries[0] = (0, heading.group(1))
        else:
            boundaries.append((heading.start(), heading.group(1)))
    for index, (start, section) in enumerate(boundaries):
        section_start = start
        end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
        while start < end:
            stop = min(start + 8000, end)
            if stop < end:
                newline = text.rfind("\n", start + 4000, stop)
                if newline >= 0:
                    stop = newline + 1
            yield section_start, start, section, text[start:stop]
            start = stop


def split_document(text, provider, checkpoint=lambda: None):
    # Reject pathological opaque tokens before invoking the tokenizer. CJK is unaffected.
    if re.search(r"[A-Za-z0-9_]{4097}", text):
        raise ValueError("Document contains an overlong unbroken token")
    splitter = SpanSplitter(provider.token_count)
    result = []
    tail_start, prior_section = None, None
    for section_start, offset, section, block in source_blocks(text):
        checkpoint()
        if not block.strip():
            tail_start = None
            continue
        if tail_start is not None and prior_section == section_start:
            # Re-split the final bounded chunk across the artificial work boundary.
            # A real heading (including repeated heading text) always resets continuity.
            result.pop()
            block = text[tail_start:offset] + block
            offset = tail_start
        contents = splitter.split_text(block)
        for content in contents:
            if len(result) >= 1000:
                raise ValueError("Document exceeds 1000 chunks")
            start, end = content.start, content.end
            if start < 0 or block[start:end] != content:
                raise ValueError("Chunk does not resolve to an exact normalized source span")
            result.append(
                Passage(
                    str(content),
                    offset + start,
                    offset + end,
                    section[:200],
                    provider.token_count("passage: " + content),
                )
            )
        # Carry exactly the recorded final span, never a separately guessed occurrence.
        tail_start = result[-1].start if contents else None
        prior_section = section_start
    if not result:
        raise ValueError("Document must produce at least one chunk")
    return result
