from __future__ import annotations

from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.language import SupportedLanguage
from app.services.retrieval_service import RetrievalResult

CLASSIFICATION_SYSTEM_TEMPLATE = (
    "Classify the support message into one concise intent label. "
    "Prefer deterministic labels used by the backend workflow: "
    "refund_request, account_security, privacy_complaint, "
    "prompt_injection, or general_support. Return only the label."
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

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", CLASSIFICATION_SYSTEM_TEMPLATE), ("human", CLASSIFICATION_HUMAN_TEMPLATE)]
)

DRAFT_RESPONSE_PROMPT = ChatPromptTemplate.from_messages(
    [("system", DRAFT_RESPONSE_SYSTEM_TEMPLATE), ("human", DRAFT_RESPONSE_HUMAN_TEMPLATE)]
)


def build_classification_prompt(input_message: str) -> str:
    prompt_value = CLASSIFICATION_PROMPT.invoke({"input_message": input_message})
    return prompt_value.to_string()


def retrieval_results_to_documents(results: list[RetrievalResult]) -> list[Document]:
    return [
        Document(
            page_content=result.content,
            metadata={
                "citation": result.citation,
                "chunk_id": str(result.chunk_id),
                "document_id": str(result.document_id),
                "document_title": result.document_title,
                "version": result.version,
                "chunk_index": result.chunk_index,
                "language": result.language.value,
                "token_count": result.token_count,
                "combined_score": result.combined_score,
            },
        )
        for result in results
    ]


def chunk_payloads_to_documents(chunks: list[dict[str, Any]]) -> list[Document]:
    documents: list[Document] = []
    for chunk in chunks:
        language = chunk.get("language")
        if isinstance(language, SupportedLanguage):
            language = language.value
        documents.append(
            Document(
                page_content=str(chunk.get("content") or ""),
                metadata={
                    "citation": str(chunk.get("citation") or "uncited"),
                    "chunk_id": str(chunk.get("chunk_id") or ""),
                    "document_id": str(chunk.get("document_id") or ""),
                    "document_title": str(chunk.get("document_title") or ""),
                    "version": chunk.get("version"),
                    "chunk_index": chunk.get("chunk_index"),
                    "language": language,
                    "token_count": chunk.get("token_count"),
                    "combined_score": chunk.get("combined_score"),
                },
            )
        )
    return documents


def build_draft_response_prompt(
    *,
    input_message: str,
    language: SupportedLanguage,
    documents: list[Document],
) -> str:
    evidence = _format_evidence(documents)
    prompt_value = DRAFT_RESPONSE_PROMPT.invoke(
        {
            "language": language.value,
            "input_message": input_message,
            "evidence": evidence,
        }
    )
    return prompt_value.to_string()


def parse_model_text(text: str) -> str:
    return StrOutputParser().invoke(text).strip()


def _format_evidence(documents: list[Document]) -> str:
    if not documents:
        return "No cited evidence was retrieved."
    lines: list[str] = []
    for index, document in enumerate(documents, start=1):
        citation = document.metadata.get("citation", "uncited")
        score = document.metadata.get("combined_score")
        score_text = f" score={score}" if score is not None else ""
        lines.append(f"[{index}] {citation}{score_text}\n{document.page_content}")
    return "\n\n".join(lines)
