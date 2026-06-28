# Attention Guardrail Trace Targets

## Goal
Make guardrail-failure attention items open the exact graph trace that produced the block instead of sending users to a generic guardrail page.

## Context
The workspace attention queue is now the backend source of truth for overview action cards. Failed graph runs, failed model calls, and failed tool calls already deep-link to traces. Guardrail failures still used a broad `guardrails` target even though `GuardrailResult` records have a required `graph_run_id`.

## Implementation
- Changed `AttentionService._guardrail_failures` to load the latest failed `GuardrailResult` row, not only the max timestamp.
- Set guardrail attention action to `Inspect trace`.
- Set `target_tab=trace` and `target_id=<graph_run_id>` for failed guardrail attention items.
- Updated attention tests to prove guardrail failures from real agent runs and manually inserted failure records point to the related trace.

## Validation
- `cd backend && uv run ruff check app/services/attention_service.py tests/test_attention.py`
- `cd backend && uv run pytest -s -q tests/test_attention.py`
- `cd frontend && npm run build`

## Results
- Ruff passed.
- Attention tests passed: 4 passed, 1 existing Starlette/httpx deprecation warning.
- Frontend production build passed.

## Browser QA
Not run for this ticket. WSL Playwright Chromium is still blocked by missing system library `libnspr4.so`, and installing the package needs sudo credentials.

## Human Review Checklist
- In the workspace overview or My Tasks attention queue, a guardrail block should take the user to the trace for the blocked run.
- The trace should contain the guardrail result, graph steps, model/tool calls, and route decision needed to debug the block.

## Follow-Up
Audit all upload/file-list frontend areas. Anything that can grow with many files or document names should be managed through folders, searchable lists, pagination, or detail drawers instead of a flat expanding panel.
