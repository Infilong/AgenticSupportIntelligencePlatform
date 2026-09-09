"""Carry source positions through LangChain's recursive splitting and token-aware merging.

The adapter is deliberately limited to literal separators retained at the end. Private
LangChain merge/join hooks are covered by compatibility tests against the installed version.
"""

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

SEPARATORS = ["\n\n", "\n", "。", "！", "？", ". ", " ", "、", "，", ""]


class SourceSpan(str):
    def __new__(cls, text, start):
        value = super().__new__(cls, text)
        value.start = start
        return value

    @property
    def end(self):
        return self.start + len(self)


class SpanSplitter(RecursiveCharacterTextSplitter):
    def __init__(self, token_count):
        super().__init__(
            chunk_size=350,
            chunk_overlap=45,
            keep_separator="end",
            length_function=token_count,
            separators=SEPARATORS,
        )

    def split_text(self, text):
        return self._partition(SourceSpan(text, 0), self._separators)

    def _partition(self, span, separators):
        separator = next(item for item in separators if not item or item in span)
        remaining = separators[separators.index(separator) + 1 :]
        # Sequential non-overlapping partitions retain their true positions even when
        # every piece is identical. Delimiters stay attached just as in LangChain.
        ends = (
            [match.end() for match in re.finditer(re.escape(separator), span)]
            if separator
            else list(range(1, len(span) + 1))
        )
        if not ends or ends[-1] != len(span):
            ends.append(len(span))
        output, pending, start = [], [], 0
        for end in ends:
            piece = SourceSpan(span[start:end], span.start + start)
            start = end
            if self._length_function(piece) < self._chunk_size:
                pending.append(piece)
                continue
            output.extend(self._merge_splits(pending, ""))
            pending = []
            output.extend(self._partition(piece, remaining) if remaining else [piece])
        output.extend(self._merge_splits(pending, ""))
        return output

    def _join_docs(self, docs, separator):
        text = super()._join_docs(docs, separator)
        if text is None:
            return None
        joined = separator.join(docs)
        leading = len(joined) - len(joined.lstrip())
        return SourceSpan(text, docs[0].start + leading)
