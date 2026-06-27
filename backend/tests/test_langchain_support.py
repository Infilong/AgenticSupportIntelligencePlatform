from uuid import uuid4

from app.core.language import SupportedLanguage
from app.services.langchain_support import (
    build_classification_prompt,
    build_draft_response_prompt,
    chunk_payloads_to_documents,
    parse_model_text,
    retrieval_results_to_documents,
)
from app.services.retrieval_service import RetrievalResult


def test_langchain_classification_prompt_contains_message_and_allowed_labels() -> None:
    prompt = build_classification_prompt("Can I get a refund within 30 days?")

    assert "refund_request" in prompt
    assert "Can I get a refund within 30 days?" in prompt


def test_retrieval_results_are_converted_to_langchain_documents() -> None:
    result = RetrievalResult(
        chunk_id=uuid4(),
        document_id=uuid4(),
        document_title="Refund Policy",
        version=2,
        chunk_index=4,
        language=SupportedLanguage.en,
        content="Refunds are available within 30 days.",
        token_count=7,
        vector_score=0.81,
        lexical_score=0.74,
        combined_score=0.76,
        citation="Refund Policy v2 #chunk-4",
    )

    documents = retrieval_results_to_documents([result])

    assert documents[0].page_content == "Refunds are available within 30 days."
    assert documents[0].metadata["citation"] == "Refund Policy v2 #chunk-4"
    assert documents[0].metadata["language"] == "en"


def test_langchain_draft_prompt_contains_language_evidence_and_citation() -> None:
    documents = chunk_payloads_to_documents(
        [
            {
                "content": "返金は購入から30日以内に申請できます。",
                "citation": "Refund Policy JA v1 #chunk-0",
                "language": SupportedLanguage.ja,
                "combined_score": 0.91,
            }
        ]
    )

    prompt = build_draft_response_prompt(
        input_message="返金はできますか？",
        language=SupportedLanguage.ja,
        documents=documents,
    )

    assert "Language: ja" in prompt
    assert "返金はできますか？" in prompt
    assert "Refund Policy JA v1 #chunk-0" in prompt
    assert "返金は購入から30日以内" in prompt


def test_langchain_output_parser_normalizes_text() -> None:
    assert parse_model_text("  refund_request\n") == "refund_request"
