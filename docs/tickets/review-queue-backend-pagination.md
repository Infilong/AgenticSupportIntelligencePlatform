# Review Queue Backend Pagination

## Goal
Prevent the human review page from becoming another unbounded browser-side list as agent runs create more review tasks and resolved audit history.

## Context
The review UI was previously improved to make individual cases understandable, but the API still returned every review in the workspace. The frontend then filtered, sorted, and sliced locally. That works for demos but is the wrong boundary for a serious operations console.

## Requirements
- Add backend query support for pending vs resolved reviews.
- Add queue filters for mine, unassigned, critical, evidence, model/budget, and language issues.
- Add backend search across review fields and graph-run context.
- Add backend sort and `limit`/`offset` pagination.
- Wire the frontend pending queue and resolved history to backend-loaded pages.
- Preserve workspace isolation and reviewer assignment rules.

## Non-goals
- No deletion for human reviews; decisions are audit evidence.
- No schema changes.
- No total-count endpoint in this ticket.
- No virtualized frontend table.

## Implementation Notes
- `GET /human-reviews` now accepts `decision`, `queue_filter`, `search`, `sort`, `limit`, and `offset`.
- `HumanReviewService.list_reviews()` builds workspace-scoped SQL filters and joins graph-run context for search.
- The frontend loads pending and resolved reviews as separate bounded pages.
- Review search resets both pages; pending filter and sort reset the pending page.
- The UI labels review summary counts as loaded counts to avoid pretending it has global totals.

## Validation
- `cd backend && uv run ruff check app/api/v1/human_reviews.py app/services/human_review_service.py tests/test_human_reviews.py` -> passed.
- `cd backend && uv run pytest -s -q tests/test_human_reviews.py` -> 9 passed, 1 warning.
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.
- `git diff --check` -> passed.

## Human Review Checklist
- Confirm queue search no longer causes the page to jump or lose input focus.
- Confirm pending Next/Previous behaves clearly when the page is full.
- Confirm resolved history remains useful for audit without loading every old decision.
- Confirm loaded-count wording is acceptable until a total-count endpoint exists.

## Interview Notes
This ticket demonstrates a backend/frontend boundary improvement: operational queues should be filtered and paginated server-side, while the frontend stays responsible for selecting and resolving a single case. It also keeps audit evidence immutable while still making large histories navigable.
