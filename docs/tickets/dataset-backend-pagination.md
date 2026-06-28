# Dataset Backend Pagination

## Goal
Move the dataset library from capped local filtering to backend-owned folder, unfiled, search, offset, and limit filtering so large import histories remain navigable and permission-scoped.

## Context
Knowledge documents now use a backend pagination pattern. Datasets are the next large resource library: users import multilingual examples, organize them into folders, delete them, and inspect examples for labels/evaluation readiness. Before this ticket, the frontend requested a capped list and then filtered locally, which can hide datasets once the workspace grows.

## Requirements
- Add backend `offset` support for dataset list queries.
- Add explicit `unfiled=true` filtering because omitted `folder_id` means all folders.
- Reject conflicting `folder_id` plus `unfiled` filters.
- Keep the existing list response shape.
- Update the dataset UI to load by selected folder, unfiled state, search, offset, and limit.
- Add Prev/Next controls to the dataset library.
- Reset the page after folder changes, search changes, import, move, and delete actions.
- Add tests for folder paging, unfiled filtering, search, and conflict rejection.

## Non-goals
- Do not paginate examples inside a selected dataset in this ticket.
- Do not convert agents or evaluations to backend pagination yet.
- Do not introduce a paginated response envelope.
- Do not refactor `frontend/src/App.tsx`.

## Design Plan
- Extend `DatasetService.list_datasets()` with `unfiled` and `offset`.
- Extend `GET /datasets` query params with:
  - `folder_id`
  - `unfiled`
  - `search`
  - `limit`
  - `offset`
- Return a 400 `dataset_filter_conflict` if `folder_id` and `unfiled=true` are both provided.
- Add `datasetPage` frontend state and `datasetListParams()`.
- Use `MAX_VISIBLE_RESOURCES` as the dataset page size.
- Keep backend folder count metadata as the displayed total for the selected folder.

## Files Changed
- `backend/app/api/v1/datasets.py`
- `backend/app/services/dataset_service.py`
- `backend/tests/test_datasets.py`
- `frontend/src/App.tsx`

## Test Plan
- `uv run pytest -s -q tests/test_datasets.py tests/test_resource_folders.py`
- `uv run ruff check .`
- `npm run typecheck`
- `npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Folder-specific dataset listing can page with `limit` and `offset`.
- Unfiled dataset listing returns only unfiled datasets.
- Search applies on the backend inside the selected folder scope.
- `folder_id` plus `unfiled=true` returns a clear 400 error.
- Dataset UI loads a backend page rather than filtering a capped local slice.
- Browser smoke remains green.

## Risks
- Selected dataset examples are still loaded as a full list. That should become its own pagination ticket if imports become very large.
- Search pages do not yet expose a filtered total; the UI allows Next when a search page is full.
- Offset pagination is acceptable for local-first v1, but cursor pagination may be better for high-volume production datasets.

## Human Review Checklist
- Confirm the dataset library page controls are understandable.
- Confirm example inspection still works after selecting a dataset from the backend-loaded page.
- Confirm `unfiled=true` matches the knowledge document API pattern.
- Confirm agents and evaluations should be the next resource libraries to adopt this pattern.

## Interview Notes
- Explain why capped client filtering can hide resources.
- Explain why the system uses backend folder counts plus page queries.
- Explain the tradeoff between simple offset pagination for v1 and cursor pagination for larger production data.
