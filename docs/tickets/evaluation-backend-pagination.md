# Evaluation Backend Pagination

## Goal
Make the Evaluation operations board scalable and folder-managed so long experiment histories do not stretch the page or require the browser to load every run before filtering.

## Context
Knowledge documents, datasets, and agents now use backend folder/search/page loading. Evaluation runs already had folder move/archive/delete lifecycle controls, but the frontend still fetched a broad bounded list and applied folder, status, view, and search filters locally. That becomes inaccurate and noisy when many regression packs, release checks, and archived experiments exist.

## Requirements
- Add backend `unfiled`, `archived_only`, `status`, `limit`, and `offset` filters for evaluation run listing.
- Keep existing `folder_id`, `search`, and `include_archived` behavior.
- Reject conflicting `folder_id` plus `unfiled` filters.
- Keep archive-first lifecycle semantics: active evaluation runs are archived, and only archived runs can be permanently deleted.
- Wire the frontend Evaluation board to load one backend-filtered page by folder, archive view, status, search, offset, and limit.
- Keep the Selected view as a local one-run inspector based on the loaded evaluation detail.
- Reset to page one when folder/search/status/archive view changes.

## Non-goals
- Do not add bulk delete or bulk archive.
- Do not change evaluation scoring, baseline modes, or JSONL schema.
- Do not add total-count endpoints for search-specific result counts.
- Do not change the agent dropdown data source in the evaluation form.

## Design Plan
- Extend `EvaluationRunner.list_runs()` with `unfiled`, `archived_only`, `status_filter`, and `offset`.
- Extend `GET /api/v1/workspaces/{workspace_id}/evaluations` query params and conflict validation.
- Add API tests for folder pagination, unfiled filtering, search, status filtering, archived-only filtering, and conflict rejection.
- Add `evaluationPage` state and `evaluationListParams()` in `frontend/src/App.tsx`.
- Replace local Evaluation board filtering with the backend response page.
- Add Previous/Next controls and backend-backed folder-count display.

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_evaluations.py tests/test_resource_folders.py`
- `cd backend && uv run ruff check .`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Evaluation list API supports folder/unfiled/archive/status/search/limit/offset filtering.
- Invalid `folder_id` plus `unfiled` returns 400 with `evaluation_filter_conflict`.
- Evaluation board renders a backend-loaded page with Previous/Next controls.
- Running, moving, archiving, and deleting evaluation runs refresh folder counts and the current list view.
- The page remains usable as evaluation history grows.

## Risks
- Search-specific total counts are still inferred by page size; a full page enables Next even if the next search page may be empty.
- Metrics shown above the evaluation list summarize the current loaded page, not all matching runs across all pages.
- The evaluation form target-agent dropdown still depends on the currently loaded agent page; a future agent picker endpoint would be better for very large agent catalogs.

## Human Review Checklist
- Confirm the Evaluation board makes folder, search, status, archive view, and pagination controls understandable.
- Confirm archive and permanent delete actions are still permission-aware and lifecycle-safe.
- Confirm Selected view still displays the selected run even when it is not on the current backend page.
- Confirm the UI no longer grows with every evaluation run.

## Interview Notes
This ticket demonstrates how to turn a demo-style history panel into an operations-grade resource library: server-owned filtering, archive-aware cleanup, folder organization, pagination, and explicit tradeoffs around counts and selected-detail views.
