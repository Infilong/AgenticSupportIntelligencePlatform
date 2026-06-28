# Trace Retrieval Evidence Cards

## Goal
Make retrieved RAG evidence first-class in the trace viewer so developers and reviewers can inspect citations, language, token counts, scores, and snippets without opening raw JSON.

## Context
The backend now proves Chinese knowledge can flow through retrieval and agent trace. The frontend trace viewer still made users infer evidence from output signals or raw JSON. For a professional AI platform, the trace page should explain how an answer was produced directly in the UI.

## Implementation
- Added a `TraceRetrievedChunk` frontend type for trace evidence payloads.
- Added `traceRetrievedChunks()` to extract retrieved chunks from graph step output JSON.
- Added `TraceEvidenceCards` to render the first three retrieved chunks with document/citation, language, token count, snippet, and vector/lexical/combined scores.
- Displayed evidence cards in both the selected-node inspector and detailed timeline.
- Added bounded styling so long multilingual snippets wrap without stretching the page.

## Backend/API Impact
No API change. The UI consumes existing `retrieved_chunks` already stored in graph step output JSON.

## Validation
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`
- `cd backend && uv run pytest -s -q tests/test_agents.py::test_support_agent_uses_chinese_knowledge_in_trace`

## Results
- Frontend build passed.
- Frontend typecheck passed.
- Chinese trace regression passed: 1 passed, 1 existing Starlette/httpx warning.

## Human Review Checklist
- Open a trace with a successful RAG retrieval step.
- Select `retrieve_evidence` in the execution navigator.
- Confirm evidence cards show language, citation/document title, token count, scores, and readable snippet.
- Confirm Chinese/Japanese snippets wrap cleanly and do not expand the page horizontally.
- Confirm raw output JSON remains available for deeper debugging.
