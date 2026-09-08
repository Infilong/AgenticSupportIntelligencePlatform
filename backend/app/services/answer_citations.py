"""Validate answer references against the evidence actually packed for the model."""

import re

from app.services.support_agent_state import SupportAgentState


def has_answer_citations(state: SupportAgentState) -> bool:
    remainder, evidence = cited_answer_evidence(state)
    # Canonical markers not removed by exact matching cannot be supported references.
    return bool(evidence) and "#chunk-" not in remainder.lower()


def cited_answer_evidence(state: SupportAgentState) -> tuple[str, list[str]]:
    """Return citation-free prose and only the nonempty packed source text it cites."""
    answer = state.get("draft_answer") or ""
    if not answer.strip():
        return answer, []
    citations: dict[str, list[str]] = {}
    for chunk in state.get("packed_context_chunks") or []:
        citation = chunk.get("citation")
        content = chunk.get("content")
        if (isinstance(citation, str) and citation.strip()
                and isinstance(content, str) and content.strip()):
            citations.setdefault(citation, []).append(content)
    evidence = []
    remainder = answer
    # Longest first prevents overlapping source titles from leaving partial references.
    for citation in sorted(citations, key=len, reverse=True):
        remainder, count = re.subn(r"(?<!\w)" + re.escape(citation) + r"(?!\w)",
                                   "", remainder)
        if count:
            evidence.extend(citations[citation])
    return remainder, evidence
