# Knowledge Document Backend Pagination

## Goal
Make the uploaded knowledge document library scale beyond a capped browser fetch by moving folder, search, unfiled, offset, and limit filtering into the backend and exposing page controls in the UI.

## Context
The platform already supports upload, edit/reindex, move, delete, and backend count metadata for knowledge documents. After adding bounded list fetches and backend folder counts, the remaining problem was that the Knowledge page still fetched a capped slice and then filtered locally. That can hide files in larger workspaces and makes folder/search controls less trustworthy.

## Requirements
- Support backend `offset` for knowledge document lists.
- Support explicit `unfiled=true` filtering because `folder_id=null` means no folder filter in query params.
- Reject conflicting `folder_id` plus `unfiled` filters.
- Preserve existing list response shape for compatibility.
- Update the Knowledge UI to load documents by selected folder, unfiled state, search term, offset, and limit.
- Add Prev/Next controls for document browsing.
- Keep backend folder count metadata as the source for folder totals.
- Add tests for folder paging, unfiled filtering, search, and conflict rejection.

## Non-goals
- Do not convert every resource list to pagination in this ticket.
- Do not introduce a paginated response envelope yet.
- Do not add search-total counts for filtered search pages.
- Do not refactor the large frontend component file.

## Design Plan
- Extend `KnowledgeService.list_documents()` with `unfiled` and `offset`.
- Extend `GET /knowledge-documents` query params with:
  - `folder_id`
  - `unfiled`
  - `search`
  - `limit`
  - `offset`
- Add a 400 response when `folder_id` and `unfiled` are both provided.
- Add `documentPage` frontend state and a `knowledgeDocumentListParams()` helper.
- Use `MAX_VISIBLE_RESOURCES` as the backend page size.
- Reset page to zero on folder/search changes and after document mutations.
- Render a compact pagination bar under the document list.

## Files Changed
- `backend/app/api/v1/knowledge.py`
- `backend/app/services/knowledge_service.py`
- `backend/tests/test_knowledge_documents.py`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`

## Test Plan
- `uv run pytest -s -q tests/test_knowledge_documents.py tests/test_resource_folders.py`
- `uv run ruff check .`
- `npm run typecheck`
- `npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Folder-specific knowledge listing can page with `limit` and `offset`.
- Unfiled knowledge listing returns only unfiled documents.
- Search applies on the backend within the selected folder scope.
- `folder_id` plus `unfiled=true` returns a clear 400 error.
- Knowledge UI loads a backend page instead of filtering a large local slice.
- Browser smoke remains green.

## Risks
- Search pages do not yet show filtered total counts. The UI allows Next when a search page is full.
- Datasets, agents, and evaluations still use the older capped-fetch pattern and should adopt this reusable pattern in later tickets.
- Offset pagination is simple and interview-defensible for local-first v1, but cursor pagination may be better for very large production histories.

## Human Review Checklist
- Confirm the Knowledge page feels understandable with folder counts plus page controls.
- Confirm `unfiled=true` is the right API shape for unfiled resources.
- Confirm existing upload/edit/delete/move flows still refresh the current document list correctly.
- Confirm this pattern should be reused for the other resource libraries.

## Interview Notes
- Explain why local filtering after capped fetches can be misleading.
- Explain why the API keeps array responses compatible while adding backend pagination controls.
- Explain why offset pagination is acceptable for the local-first v1 and where cursor pagination would fit later.
