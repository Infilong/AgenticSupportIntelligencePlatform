from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, PromptTemplate
from app.services.model_provider import ModelProvider
from app.services.retrieval_service import RetrievalResult, RetrievalService


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

CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages(
    [("system", CLASSIFICATION_SYSTEM_TEMPLATE), ("human", CLASSIFICATION_HUMAN_TEMPLATE)]
).partial(format_instructions=CLASSIFICATION_OUTPUT_PARSER.get_format_instructions())

DRAFT_RESPONSE_PROMPT = ChatPromptTemplate.from_messages(
    [("system", DRAFT_RESPONSE_SYSTEM_TEMPLATE), ("human", DRAFT_RESPONSE_HUMAN_TEMPLATE)]
)


@dataclass(frozen=True)
class LangChainModelCall:
    content: str
    ai_run: AIRun
    prompt_text: str
    structured_output: dict[str, Any] | None = None


def build_classification_prompt(input_message: str) -> str:
    prompt_value = CLASSIFICATION_PROMPT.invoke({"input_message": input_message})
    return prompt_value.to_string()


def run_classification_chain(
    *,
    provider: ModelProvider,
    workspace_id: UUID,
    language: SupportedLanguage,
    input_message: str,
    graph_run_id: UUID,
    prompt_template: PromptTemplate | None,
    completion_text: str,
    model: str = "mock-cheap",
) -> LangChainModelCall:
    captured: dict[str, Any] = {}

    def call_model(prompt_value: Any) -> str:
        prompt_text = prompt_value.to_string()
        response = provider.complete(
            workspace_id=workspace_id,
            purpose="classification",
            language=language,
            prompt=prompt_text,
            model=model,
            graph_run_id=graph_run_id,
            prompt_template=prompt_template,
            completion_text=completion_text,
        )
        captured["prompt_text"] = prompt_text
        captured["ai_run"] = response.ai_run
        return response.content

    chain = CLASSIFICATION_PROMPT | RunnableLambda(call_model) | CLASSIFICATION_OUTPUT_PARSER
    parsed = chain.invoke({"input_message": input_message})
    return LangChainModelCall(
        content=parsed.intent,
        ai_run=captured["ai_run"],
        prompt_text=captured["prompt_text"],
        structured_output=parsed.model_dump(),
    )


def parse_classification_output(text: str) -> ClassificationOutput:
    return CLASSIFICATION_OUTPUT_PARSER.invoke(text)


def create_search_documents_tool(*, db, workspace_id: UUID) -> StructuredTool:
    """Create a workspace-scoped LangChain tool around the app retrieval service."""

    def search_documents(
        query: str,
        language: str,
        top_k: int = 4,
        min_score: float = 0.2,
    ) -> dict[str, Any]:
        """Search workspace knowledge documents and return cited chunks."""
        normalized_language = SupportedLanguage(language)
        retrieval = RetrievalService(db).search(
            workspace_id=workspace_id,
            query=query,
            language=normalized_language,
            top_k=top_k,
            min_score=min_score,
            document_id=None,
        )
        return {
            "framework": "langchain_core.tools.StructuredTool",
            "tool_name": "search_documents",
            "trace_id": str(retrieval.trace_id),
            "no_source": retrieval.no_source,
            "result_count": len(retrieval.results),
            "results": [_retrieval_result_payload(result) for result in retrieval.results],
        }

    return StructuredTool.from_function(
        func=search_documents,
        name="search_documents",
        description=(
            "Search workspace-scoped support knowledge and return cited chunks. "
            "The backend enforces workspace isolation before the tool is created."
        ),
    )


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


def run_draft_response_chain(
    *,
    provider: ModelProvider,
    workspace_id: UUID,
    language: SupportedLanguage,
    input_message: str,
    documents: list[Document],
    graph_run_id: UUID,
    prompt_template: PromptTemplate | None,
    completion_text: str,
    model: str = "mock-standard",
) -> LangChainModelCall:
    captured: dict[str, Any] = {}

    def call_model(prompt_value: Any) -> str:
        prompt_text = prompt_value.to_string()
        response = provider.complete(
            workspace_id=workspace_id,
            purpose="draft_response",
            language=language,
            prompt=prompt_text,
            model=model,
            graph_run_id=graph_run_id,
            prompt_template=prompt_template,
            completion_text=completion_text,
        )
        captured["prompt_text"] = prompt_text
        captured["ai_run"] = response.ai_run
        return response.content

    chain = DRAFT_RESPONSE_PROMPT | RunnableLambda(call_model) | StrOutputParser()
    content = chain.invoke(
        {
            "language": language.value,
            "input_message": input_message,
            "evidence": _format_evidence(documents),
        }
    ).strip()
    return LangChainModelCall(
        content=content,
        ai_run=captured["ai_run"],
        prompt_text=captured["prompt_text"],
    )


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


def _retrieval_result_payload(result: RetrievalResult) -> dict[str, Any]:
    return {
        "chunk_id": str(result.chunk_id),
        "document_id": str(result.document_id),
        "document_title": result.document_title,
        "version": result.version,
        "chunk_index": result.chunk_index,
        "language": result.language.value,
        "content": result.content,
        "token_count": result.token_count,
        "vector_score": result.vector_score,
        "lexical_score": result.lexical_score,
        "combined_score": result.combined_score,
        "citation": result.citation,
    }
