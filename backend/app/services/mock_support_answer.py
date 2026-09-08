"""Deterministic source excerpts for mock runs; no inferred support-policy facts."""

from app.core.language import SupportedLanguage

MAX_EXCERPT_CHARS = 800


def mock_support_answer(
    *, language: SupportedLanguage, intent: str | None,
    input_message: str, chunks: list[dict],
) -> str:
    # Intent and user wording must never manufacture facts absent from retrieved evidence.
    labels = {
        SupportedLanguage.en: "Mock response — source excerpt (not a policy decision):",
        SupportedLanguage.ja: "模擬応答 — 資料の抜粋（ポリシー判断ではありません）：",
        SupportedLanguage.zh: "模拟回答 — 资料摘录（不代表政策判断）：",
    }
    missing = {
        SupportedLanguage.en: "No citable evidence is available. Human review is required.",
        SupportedLanguage.ja: "引用できる資料がありません。担当者による確認が必要です。",
        SupportedLanguage.zh: "没有可引用的资料，需要人工审核。",
    }
    for chunk in chunks:
        content = str(chunk.get("content") or "").strip()
        citation = str(chunk.get("citation") or "").strip()
        if not content or not citation:
            continue
        excerpt = content[:MAX_EXCERPT_CHARS]
        if len(content) > MAX_EXCERPT_CHARS:
            excerpt += "…"
        return f"{labels[language]}\n{excerpt}\n{citation}"
    return missing[language]
