from enum import StrEnum


class SupportedLanguage(StrEnum):
    en = "en"
    ja = "ja"
    zh = "zh"


class LanguageDetectionError(ValueError):
    pass


def detect_language(text: str) -> SupportedLanguage:
    compact = "".join(ch for ch in text.strip() if not ch.isspace())
    if not compact:
        raise LanguageDetectionError("Cannot detect language from empty text.")

    kana_count = sum(_is_japanese_kana(ch) for ch in compact)
    cjk_count = sum(_is_cjk_ideograph(ch) for ch in compact)
    latin_count = sum(ch.isascii() and ch.isalpha() for ch in compact)

    if kana_count > 0:
        return SupportedLanguage.ja
    if cjk_count > 0:
        return SupportedLanguage.zh
    if latin_count > 0:
        return SupportedLanguage.en
    raise LanguageDetectionError("Cannot detect one of the supported languages.")


def detect_language_for_messages(messages: list[str]) -> SupportedLanguage:
    joined = "\n".join(message for message in messages if message.strip())
    return detect_language(joined)


def _is_japanese_kana(ch: str) -> bool:
    codepoint = ord(ch)
    return 0x3040 <= codepoint <= 0x30FF or 0x31F0 <= codepoint <= 0x31FF


def _is_cjk_ideograph(ch: str) -> bool:
    codepoint = ord(ch)
    return (
        0x3400 <= codepoint <= 0x4DBF
        or 0x4E00 <= codepoint <= 0x9FFF
        or 0xF900 <= codepoint <= 0xFAFF
    )


def select_support_language(text: str, requested: str | None = None) -> dict[str, str]:
    language = SupportedLanguage(requested) if requested is not None else detect_language(text)
    return {"detected_language": language.value,
            "language_source": "requested" if requested is not None else "detected"}
