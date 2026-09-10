"""Small script-based default for the three supported question languages."""

import re


def question_language(text: str, fallback: str = "en") -> str:
    # Kana distinguish ordinary Japanese sentences from Chinese Han text.
    # Han-only Japanese names/phrases are ambiguous; callers can choose explicitly.
    if re.search(r"[\u3040-\u30ff\uff66-\uff9f]", text):
        return "ja"
    if re.search(r"[\u3400-\u4dbf\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return fallback
