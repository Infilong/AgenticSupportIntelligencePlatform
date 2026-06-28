# Backend-Backed Overview Attention

## Goal
Make the Overview dashboard use the same backend-ranked attention queue as the My Tasks page, so operators see one consistent source of truth for workspace issues.

## Context
The backend already exposes `/attention` through `AttentionService`, with items for pending reviews, assigned reviews, failed graph runs, failed model calls, tool failures, guardrail failures, failed document indexing, and evaluation failures. The My Tasks page used this API, but the Overview page still rebuilt a separate local list from partial frontend state.

## Requirements
- Overview needs-attention cards must be backed by `attentionSummary.items`.
- Overview recommended action should prefer the top backend attention item when one exists.
- Clicking an attention item should open the target operations page through the same behavior used by My Tasks.
- Trace-targeted attention items should load the trace when a target run id exists.
- Do not add placeholder task data.

## Non-goals
- Do not change the backend attention model in this ticket.
- Do not redesign the full dashboard.
- Do not add browser automation while Playwright is blocked in WSL.

## Implementation
- Promoted `openAttentionItem()` to a shared app-level helper used by both Overview and My Tasks.
- Added shared severity-to-badge tone mapping for attention items.
- Replaced Overview's local attention heuristics with `attentionSummary.items`.
- Overview's primary recommendation now opens the highest-ranked backend task before falling back to setup or agent-run actions.

## Validation
- `cd frontend && npm run build` passed.
- `cd backend && uv run pytest -s -q tests/test_attention.py` passed: 3 passed, 1 warning.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm Overview and My Tasks show the same open operational issues.
- Confirm clicking backend attention cards opens Reviews, Guardrails, Costs, Tools, Documents, Evaluations, or Trace as appropriate.
- Confirm setup guidance still appears when there are no backend attention items.

## Interview Notes
This ticket demonstrates backend-supported product logic. A serious operations dashboard should not recompute task state independently in the browser; the backend owns workspace-scoped task prioritization and the frontend renders it consistently.
