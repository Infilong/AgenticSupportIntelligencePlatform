"""Normalized-text character offsets, model-token bounds and multilingual lexical terms."""

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


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
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=45,
        keep_separator="end",
        length_function=provider.token_count,
        separators=["\n\n", "\n", "。", "！", "？", ". ", " ", "、", "，", ""],
    )
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
        previous_start = -1
        contents = splitter.split_text(block)
        for content in contents:
            if len(result) >= 1000:
                raise ValueError("Document exceeds 1000 chunks")
            start = block.find(content, previous_start + 1)
            end = start + len(content)
            if start < 0 or block[start:end] != content:
                raise ValueError("Chunk does not resolve to an exact normalized source span")
            result.append(
                Passage(
                    content,
                    offset + start,
                    offset + end,
                    section[:200],
                    provider.token_count("passage: " + content),
                )
            )
            previous_start = start
        # Repeated text may have several exact occurrences. Carry the final occurrence,
        # not the first matching offset, so repetitive documents cannot grow the work block.
        tail_start = offset + block.rfind(contents[-1]) if contents else None
        prior_section = section_start
    if not result:
        raise ValueError("Document must produce at least one chunk")
    return result
