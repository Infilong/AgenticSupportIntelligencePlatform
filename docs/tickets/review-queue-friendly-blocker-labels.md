# Review Queue Friendly Blocker Labels

## Goal
Remove raw guardrail/review reason codes from the Human Review queue so reviewer-facing metadata reads like product language instead of backend implementation details.

## Context
The Human Review page had already been redesigned into a proper queue and selected-case workbench, but the queue metadata still rendered raw reason fragments such as `prompt_injection`, `citation_required`, or `unsupported_answer`. The user previously called this confusing, and the active goal requires reviewer workflows to be understandable without reading backend codes.

## Requirements
- Keep backend reason codes unchanged for traceability and tests.
- Render friendly labels in reviewer-facing queue metadata and selected-case summary.
- Render classification intent/area/risk as readable labels instead of raw snake_case values.
- Add browser coverage that a prompt-injection review shows friendly language and does not expose the raw `prompt_injection` code on the Review page.

## Non-goals
- Do not change review routing logic.
- Do not change stored `HumanReview.reason` values.
- Do not redesign the whole Review page in this ticket.

## Implementation Notes
- Added `friendlyReviewReasonSummary` and `friendlySignalValue` in `frontend/src/App.tsx`.
- Reused existing `friendlyGuardrailName` mapping so queue summaries, blocker chips, and selected-case summaries share terminology.
- Extended the Playwright smoke test to assert friendly Review queue language.

## Verification
- `cd frontend && npm test -- --run` - typecheck passed
- `cd frontend && npm run build` - production build passed
- `docker compose up -d --build api frontend` - rebuilt stale local services before browser QA
- `make frontend-e2e-docker` - 1 passed
