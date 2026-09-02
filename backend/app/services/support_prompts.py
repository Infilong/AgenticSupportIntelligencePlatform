from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.core.language import SupportedLanguage
from app.models.ai import PromptTemplate
from app.services.prompt_runtime import compile_prompt_template


class ClassificationOutput(BaseModel):
    intent: str = Field(description="Stable intent label used by backend routing.")
    sentiment: str = Field(description="Customer sentiment: neutral, frustrated, angry, or urgent.")
    product_area: str = Field(
        description="Product or operational area such as billing or security."
    )
    safety_risk: str = Field(description="Safety or business risk level: low, medium, or high.")
    escalation_needed: bool = Field(description="Whether a human escalation is needed.")
    confidence: float = Field(ge=0.0, le=1.0, description="Classifier confidence from 0 to 1.")
    rationale: str = Field(description="Short reviewer-readable reason for the classification.")


CLASSIFICATION_OUTPUT_PARSER = PydanticOutputParser(pydantic_object=ClassificationOutput)

CLASSIFICATION_SYSTEM_TEMPLATE = (
    "Classify the support message for an AI support operations workflow. "
    "Return only valid JSON that matches these format instructions:\n"
    "{format_instructions}"
)
CLASSIFICATION_HUMAN_TEMPLATE = "Support message:\n{input_message}"
CLASSIFICATION_TEMPLATE_TEXT = (
    f"system: {CLASSIFICATION_SYSTEM_TEMPLATE}\n"
    f"human: {CLASSIFICATION_HUMAN_TEMPLATE}"
)

DRAFT_RESPONSE_SYSTEM_TEMPLATE = (
    "Draft a same-language support answer using only the cited evidence. "
    "Do not invent policy details. If the evidence is insufficient, say the "
    "case should be reviewed by a human support specialist."
)
DRAFT_RESPONSE_HUMAN_TEMPLATE = (
    "Language: {language}\n"
    "User message:\n{input_message}\n\n"
    "Cited evidence:\n{evidence}"
)
DRAFT_RESPONSE_TEMPLATE_TEXT = (
    f"system: {DRAFT_RESPONSE_SYSTEM_TEMPLATE}\n"
    f"human: {DRAFT_RESPONSE_HUMAN_TEMPLATE}"
)


def build_classification_prompt(
    input_message: str, prompt_template: PromptTemplate | None = None
) -> str:
    prompt_value = classification_prompt(prompt_template).invoke(
        {"input_message": input_message}
    )
    return prompt_value.to_string()


def build_draft_response_prompt(
    *,
    input_message: str,
    language: SupportedLanguage,
    documents: list[Document],
    prompt_template: PromptTemplate | None = None,
) -> str:
    prompt_value = draft_response_prompt(prompt_template).invoke(
        {
            "language": language.value,
            "input_message": input_message,
            "evidence": format_evidence(documents),
        }
    )
    return prompt_value.to_string()


def classification_prompt(prompt_template: PromptTemplate | None) -> ChatPromptTemplate:
    prompt = compile_prompt_template(
        name="support_intent_classifier",
        template_text=(
            prompt_template.template_text if prompt_template else CLASSIFICATION_TEMPLATE_TEXT
        ),
    )
    if "format_instructions" in prompt.input_variables:
        prompt = prompt.partial(
            format_instructions=CLASSIFICATION_OUTPUT_PARSER.get_format_instructions()
        )
    return prompt


def draft_response_prompt(prompt_template: PromptTemplate | None) -> ChatPromptTemplate:
    return compile_prompt_template(
        name="support_response_drafter",
        template_text=(
            prompt_template.template_text if prompt_template else DRAFT_RESPONSE_TEMPLATE_TEXT
        ),
    )


def format_evidence(documents: list[Document]) -> str:
    if not documents:
        return "No cited evidence was retrieved."
    lines: list[str] = []
    for index, document in enumerate(documents, start=1):
        citation = document.metadata.get("citation", "uncited")
        score = document.metadata.get("combined_score")
        score_text = f" score={score}" if score is not None else ""
        lines.append(f"[{index}] {citation}{score_text}\n{document.page_content}")
    return "\n\n".join(lines)
