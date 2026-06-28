# Backend Resource Folder Count Metadata

## Goal
Make folder-managed resource libraries accurate as workspaces grow beyond the frontend fetch limit. Folder counts must come from backend workspace-scoped counts, not only from the currently loaded resource rows.

## Context
The previous ticket added bounded resource list fetches with `limit=500`. That protects the UI from unbounded loading, but it also means frontend-derived folder counts can be wrong once a workspace has more resources than the fetch limit. A professional admin console must keep organization controls truthful before users move or delete resources.

## Requirements
- Add a backend endpoint for per-resource-type folder count summaries.
- Keep permissions aligned with existing folder list read permissions.
- Count all resources in a workspace for the resource type, including unfiled resources.
- Return per-folder counts without changing existing list response shapes.
- Update the frontend folder panel to use backend counts when available.
- Refresh counts after create, move, archive, delete, upload, import, and evaluation actions.
- Preserve fallback counts from loaded rows if count metadata is unavailable.

## Non-goals
- Do not replace all list endpoints with paginated envelope responses yet.
- Do not add cursor pagination in this ticket.
- Do not add backend search count totals for every filter combination.
- Do not refactor the large frontend component file.

## Design Plan
- Add `ResourceFolderCountSummaryResponse` and `ResourceFolderCountResponse` schemas.
- Add `ResourceFolderService.count_resources()` using SQL `count` and `group_by` per resource type.
- Add `GET /api/v1/workspaces/{workspace_id}/resource-folders/counts?resource_type=...`.
- Reuse `_require_resource_folder_read()` so counts require the same read permission as folder lists.
- Store count summaries in frontend state keyed by `ResourceType`.
- Update `resourceItemCount()` to prefer backend summary counts and fall back to loaded-row counts.

## Files Changed
- `backend/app/api/v1/folders.py`
- `backend/app/schemas/folder.py`
- `backend/app/services/folder_service.py`
- `backend/tests/test_resource_folders.py`
- `frontend/src/App.tsx`

## Test Plan
- `uv run pytest -s -q tests/test_resource_folders.py`
- `uv run ruff check .`
- `npm run typecheck`
- `npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- A bounded list can return one row while folder count metadata still reports the true total.
- Folder counts include total, unfiled, and per-folder counts.
- Reviewers without `data:read` cannot retrieve dataset folder counts.
- Existing folder lifecycle and resource-management tests still pass.
- Frontend folder counts refresh after resource lifecycle actions.
- Browser smoke remains green.

## Risks
- Search-specific totals are still client-side for now; a future paginated envelope should include filtered totals.
- Count queries are fine for local-first v1 but may need indexes, caching, or materialized counters at larger scale.
- Evaluation and agent counts include archived records because folder deletion safety should reflect all assigned resources.

## Human Review Checklist
- Confirm folder counts now stay accurate when list fetches are capped.
- Confirm permission behavior matches folder list permissions.
- Confirm archived resources should count as folder contents.
- Confirm the next pagination ticket can wait until the UI needs page-by-page browsing.

## Interview Notes
- Explain why backend-derived counts are necessary after adding bounded list fetches.
- Explain how permission checks were reused instead of duplicated.
- Explain the tradeoff between simple aggregate counts for v1 and more complex paginated/filter-count APIs later.
