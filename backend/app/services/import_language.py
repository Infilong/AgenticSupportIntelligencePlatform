"""Prepare message languages before publishing any examples from an import."""

from app.core.language import SupportedLanguage, detect_language, detect_language_for_messages
from app.services.import_parser import ParsedExample

PreparedExample = tuple[ParsedExample, SupportedLanguage, list[SupportedLanguage]]


def prepare_import_languages(examples: list[ParsedExample]) -> list[PreparedExample]:
    prepared = []
    for example in examples:
        if example.language is not None:
            prepared.append((example, example.language, [example.language] * len(example.messages)))
            continue
        language = detect_language_for_messages([message.content for message in example.messages])
        message_languages = []
        for message in example.messages:
            # Digits, punctuation and emoji carry no independent language signal.
            # Alphabetic text still goes through detection; never mask an unsupported script.
            neutral = bool(message.content.strip()) and not any(
                character.isalpha() for character in message.content
            )
            message_languages.append(language if neutral else detect_language(message.content))
        prepared.append((example, language, message_languages))
    return prepared
