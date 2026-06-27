SUPPORTED_DOCUMENT_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "text/md",
    "markdown",
}


class DocumentParseError(ValueError):
    pass


def parse_text_document(*, content: str, content_type: str) -> str:
    normalized_type = content_type.strip().lower()
    if normalized_type not in SUPPORTED_DOCUMENT_CONTENT_TYPES:
        raise DocumentParseError(f"Unsupported document content type: {content_type}")

    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise DocumentParseError("Document content cannot be blank.")
    return normalized
