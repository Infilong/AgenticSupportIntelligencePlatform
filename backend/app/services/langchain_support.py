from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool

from app.core.language import SupportedLanguage
from app.models.ai import AIRun, PromptTemplate
from app.services.model_provider import ModelProvider
from app.services.retrieval_service import RetrievalResult, RetrievalService
from app.services.support_prompts import (
    CLASSIFICATION_OUTPUT_PARSER,
    ClassificationOutput,
    classification_prompt,
    draft_response_prompt,
    format_evidence,
)


@dataclass(frozen=True)
class LangChainModelCall:
    content: str
    ai_run: AIRun
    prompt_text: str
    structured_output: dict[str, Any] | None = None


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
    model_config_id: UUID | None = None,
) -> LangChainModelCall:
    captured: dict[str, Any] = {}
    prompt = classification_prompt(prompt_template)

    def call_model(prompt_value: Any) -> str:
        prompt_text = prompt_value.to_string()
        response = provider.complete(
            workspace_id=workspace_id,
            purpose="classification",
            language=language,
            prompt=prompt_text,
            model=model,
            model_config_id=model_config_id,
            graph_run_id=graph_run_id,
            prompt_template=prompt_template,
            completion_text=completion_text,
        )
        captured["prompt_text"] = prompt_text
        captured["ai_run"] = response.ai_run
        return response.content

    chain = prompt | RunnableLambda(call_model) | CLASSIFICATION_OUTPUT_PARSER
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
    model_config_id: UUID | None = None,
) -> LangChainModelCall:
    captured: dict[str, Any] = {}
    prompt = draft_response_prompt(prompt_template)

    def call_model(prompt_value: Any) -> str:
        prompt_text = prompt_value.to_string()
        response = provider.complete(
            workspace_id=workspace_id,
            purpose="draft_response",
            language=language,
            prompt=prompt_text,
            model=model,
            model_config_id=model_config_id,
            graph_run_id=graph_run_id,
            prompt_template=prompt_template,
            completion_text=completion_text,
        )
        captured["prompt_text"] = prompt_text
        captured["ai_run"] = response.ai_run
        return response.content

    chain = prompt | RunnableLambda(call_model) | StrOutputParser()
    content = chain.invoke(
        {
            "language": language.value,
            "input_message": input_message,
            "evidence": format_evidence(documents),
        }
    ).strip()
    return LangChainModelCall(
        content=content,
        ai_run=captured["ai_run"],
        prompt_text=captured["prompt_text"],
    )


def parse_model_text(text: str) -> str:
    return StrOutputParser().invoke(text).strip()


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
