from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate


class PromptTemplateValidationError(ValueError):
    pass


@dataclass(frozen=True)
class PromptContract:
    required_variables: frozenset[str]
    allowed_variables: frozenset[str]


PROMPT_CONTRACTS = {
    "support_intent_classifier": PromptContract(
        required_variables=frozenset({"input_message"}),
        allowed_variables=frozenset({"input_message", "format_instructions"}),
    ),
    "support_response_drafter": PromptContract(
        required_variables=frozenset({"input_message"}),
        allowed_variables=frozenset({"input_message", "language", "evidence"}),
    ),
}

_ROLE_MARKER = re.compile(r"(?m)^(system|human):[ \t]*")


def compile_prompt_template(*, name: str, template_text: str) -> ChatPromptTemplate:
    messages = _parse_messages(template_text)
    prompt = ChatPromptTemplate.from_messages(messages)
    _validate_variables(name=name, variables=set(prompt.input_variables))
    return prompt


def validate_prompt_template(*, name: str, template_text: str) -> None:
    compile_prompt_template(name=name, template_text=template_text)


def _parse_messages(template_text: str) -> list[tuple[str, str]]:
    source = template_text.strip()
    matches = list(_ROLE_MARKER.finditer(source))
    if not matches:
        raise PromptTemplateValidationError(
            "Prompt source must contain a 'system:' or 'human:' role marker."
        )
    if source[: matches[0].start()].strip():
        raise PromptTemplateValidationError("Prompt source cannot precede the first role marker.")

    messages: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        body = source[body_start:body_end].strip()
        if not body:
            raise PromptTemplateValidationError(
                f"Prompt role '{match.group(1)}' must contain text."
            )
        messages.append((match.group(1), body))
    return messages


def _validate_variables(*, name: str, variables: set[str]) -> None:
    contract = PROMPT_CONTRACTS.get(name)
    if contract is None:
        supported = ", ".join(sorted(PROMPT_CONTRACTS))
        raise PromptTemplateValidationError(
            f"Unsupported prompt template name '{name}'. Supported names: {supported}."
        )

    missing = contract.required_variables - variables
    if missing:
        names = ", ".join(f"{{{item}}}" for item in sorted(missing))
        raise PromptTemplateValidationError(
            f"Prompt template is missing required variables: {names}."
        )

    unsupported = variables - contract.allowed_variables
    if unsupported:
        names = ", ".join(f"{{{item}}}" for item in sorted(unsupported))
        allowed = ", ".join(f"{{{item}}}" for item in sorted(contract.allowed_variables))
        raise PromptTemplateValidationError(
            f"Prompt template contains unsupported variables: {names}. "
            f"Allowed variables: {allowed}."
        )
