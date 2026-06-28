# CJK Sentence-Aware Chunking

## Goal
Improve Japanese and Chinese knowledge-document chunks so the RAG inspector and retrieval evidence read like real policy snippets instead of character-window fragments with repeated boundary text.

## Context
The previous CJK chunker used fixed character windows with overlap. That is simple, but for Japanese and Chinese it can split sentences in awkward places and repeat boundary characters between adjacent chunks. The user specifically noticed Chinese demo chunks looking terrible and duplicated. Since multilingual support is a first-class project requirement, chunk quality matters for both portfolio credibility and retrieval quality.

## Implementation
- Kept English word-window chunking unchanged.
- Replaced the normal Japanese/Chinese path with sentence-aware CJK packing.
- Added `cjk_sentence_window` chunk metadata with sentence counts and character offsets.
- Kept a `cjk_long_sentence_window` fallback for unusually long CJK sentences that exceed the token budget by themselves.
- Fixed CJK token accounting to use the actual document language for Japanese and Chinese chunks instead of always estimating as Chinese.
- Added regression tests for sentence-boundary chunks, duplicate-overlap avoidance, and language-specific token counts.

## Validation
- `cd backend && uv run ruff check app/services/chunking.py tests/test_knowledge_documents.py`
- `cd backend && uv run pytest -s -q tests/test_knowledge_documents.py`
- `cd backend && uv run pytest -s -q tests/test_knowledge_documents.py tests/test_retrieval.py tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs`

## Results
- Ruff passed.
- Knowledge document tests passed: 14 passed, 1 existing Starlette/httpx warning.
- Related RAG/agent tests passed: 21 passed, 1 existing Starlette/httpx warning.

## Design Reasoning
CJK languages cannot rely on whitespace tokenization. Sentence-aware chunking produces cleaner citation units, avoids duplicated overlap text in the UI, and reduces unnecessary repeated prompt tokens when chunks are packed into RAG context. Long-sentence fallback keeps the chunker bounded even when source text has no punctuation.

## Human Review Checklist
- Upload or reindex a Chinese knowledge document with several policy sentences.
- Confirm the Knowledge chunk inspector shows complete sentence-like chunks rather than repeated partial phrases.
- Run a Chinese support query and confirm citations still appear in the trace.

## Known Limitations
This is still lightweight local-first chunking. It does not use a full Japanese or Chinese morphological analyzer. A production search system could later replace this with language-specific segmenters, rerankers, or a managed search engine.
