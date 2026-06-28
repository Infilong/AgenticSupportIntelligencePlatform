# Runtime Catalog Total Count Envelope

## Goal
Make Tools and Guardrails catalog pagination truthful by returning backend-owned page metadata instead of bare arrays. Operators should see how many matching runtime assets exist and the UI should disable Next based on backend truth, not a page-size guess.

## Context
The runtime catalog pagination ticket added backend `search`, `view`, `limit`, and `offset` controls for Tools and Guardrails. It intentionally left total-count metadata out. After the Review queue adopted an envelope, the same pattern should be applied to runtime catalogs because these pages are core admin/developer controls.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/tools` to return `items`, `total`, `limit`, `offset`, and `has_next`.
- Change `GET /api/v1/workspaces/{workspace_id}/guardrails` to return the same envelope.
- Keep workspace-scoped resolved catalog behavior, including workspace tool configs and guardrail policies.
- Keep search/view filters identical between listed items and totals.
- Update the frontend Tools and Guardrails pages to render matching totals and use backend `has_next`.
- Update tests to assert envelope metadata and empty pages.

## Non-goals
- Do not add folders to runtime catalogs; tools and guardrails are runtime definitions, not uploaded resources.
- Do not change tool execution, guardrail routing, or policy configuration semantics.
- Do not migrate all remaining paginated APIs in this ticket.

## Implementation Summary
- Added `ToolCatalogListResponse` and `GuardrailCatalogListResponse`.
- Added `ToolService.count_tools()` and `GuardrailCatalogService.count_guardrails()` backed by shared filtered catalog builders.
- Updated runtime catalog routes to return page envelopes.
- Updated React catalog loaders to consume envelopes, track totals, and use backend `has_next`.
- Added clear helpers so totals do not linger after permission/workspace changes.

## Validation
- Backend: `uv run pytest -s -q tests/test_tools.py tests/test_guardrails.py`
- Backend lint: `uv run ruff check app tests/test_tools.py tests/test_guardrails.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This is an API contract change for runtime catalog list endpoints. In-repo callers are updated, but external clients must read `items`.
- Counts are computed by resolving the small runtime catalog and filtering it in service memory. That is acceptable for v1 runtime definitions; uploaded/growing resources need database counts.

## Human Review Checklist
- Confirm Tools and Guardrails show clear `shown of total` counts.
- Confirm Next is disabled on an empty/final page.
- Confirm external API docs should eventually document list envelopes consistently across all paginated APIs.

## Interview Notes
This ticket demonstrates the difference between runtime catalogs and uploaded resources. Runtime assets are bounded definitions with workspace-specific overrides, so in-memory filtered counts are acceptable. Database-backed count queries are still required for user-generated resources that can grow unbounded.
