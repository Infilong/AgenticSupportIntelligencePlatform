# Review Queue Total Count Envelope

## Goal
Make the human review queue accurate as review history grows by returning backend-owned pagination metadata instead of bare arrays. Operators should see how many matching pending or resolved reviews exist and the UI should know whether a next page exists without guessing from page length.

## Context
The previous review pagination ticket added backend `limit` and `offset` filtering but intentionally did not add total counts. That left the frontend with loaded-count wording and `items.length === page_size` next-page inference. The active product goal is a professional AI operations console, so high-volume review queues need truthful counts and stable navigation.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/human-reviews` from a bare array to an envelope with `items`, `total`, `limit`, `offset`, and `has_next`.
- Keep all filters workspace-scoped and aligned between list and count queries.
- Preserve pending/resolved, queue filter, search, sort, limit, and offset behavior.
- Update the frontend review queue to show matching totals and disable Next using backend `has_next`.
- Update focused tests to prove total counts, offsets, and no cross-workspace leakage.

## Non-goals
- Do not add total-count envelopes for every resource in this ticket.
- Do not change review resolution, assignment, or guardrail routing semantics.
- Do not add cursor pagination; offset pagination remains acceptable for the local-first v1.

## Implementation Summary
- Added `HumanReviewListResponse` with page metadata.
- Added `HumanReviewService.count_reviews()` using the same filter helper as `list_reviews()`.
- Updated the list route to return an envelope and compute `has_next` from `offset + len(items) < total`.
- Updated the React review queue to keep pending/resolved totals and `has_next` state.
- Updated human-review tests to assert the new envelope.

## Validation
- Backend: `uv run pytest -s -q tests/test_human_reviews.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This is an API contract change for `/human-reviews`; all current in-repo callers were updated, but external clients would need to read `items`.
- Count queries duplicate the filtered list join shape; future review filters must update the shared filter helper to avoid drift.

## Human Review Checklist
- Confirm the Review page wording is clearer with matching totals.
- Confirm page navigation no longer offers a fake next page when there are exactly page-size items.
- Confirm this pattern should be reused for prompts, models, audit logs, costs, tools, guardrails, and resource libraries.

## Interview Notes
This ticket shows a practical backend/frontend boundary: the backend owns pagination truth and workspace-scoped counts, while the frontend renders bounded pages. It is a small change, but it reflects production console thinking: operators need reliable numbers, not client-side guesses.
