"""Detect answer prose language without letting known citation titles change the result."""

import re
from collections.abc import Iterable

from app.core.language import SupportedLanguage, detect_language


def detect_answer_language(answer: str, citations: Iterable[str] = ()) -> SupportedLanguage:
    prose = answer
    known = {citation for citation in citations
             if isinstance(citation, str) and "#chunk-" in citation}
    for citation in sorted(known, key=len, reverse=True):
        prose = re.sub(r"(?<!\w)" + re.escape(citation) + r"(?!\w)", "", prose)
    # Citation-only output has no detectable prose and must not pass language preservation.
    return detect_language(prose)
