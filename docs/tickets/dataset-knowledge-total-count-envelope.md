# Dataset and Knowledge Total Count Envelope

## Goal
Make dataset imports and knowledge document libraries truthful under backend pagination by returning page metadata instead of bare arrays. Large uploaded/imported resource areas should stay folder-managed and bounded instead of growing into long flat frontend lists.

## Context
The app already has resource folders for datasets, knowledge documents, agent configs, and evaluation runs. Dataset and knowledge routes supported `folder_id`, `unfiled`, `search`, `limit`, and `offset`, and the frontend used those filters. They still returned bare arrays, so the UI guessed Next-page availability from the current page length or folder-count summaries. That becomes inaccurate when search is active and weakens the large-workspace story.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/datasets` to return `items`, `total`, `limit`, `offset`, and `has_next`.
- Change `GET /api/v1/workspaces/{workspace_id}/knowledge-documents` to return the same envelope.
- Preserve folder, unfiled, search, limit, offset, and workspace isolation behavior.
- Keep folder validation and folder/unfiled conflict handling.
- Update the frontend dataset and document panels to display server-backed totals.
- Make Next buttons use backend `has_next`, not local page-size guesses.
- Keep imported datasets and uploaded knowledge documents organized by folders as their counts grow.

## Non-goals
- Do not redesign the full dataset or document UI in this ticket.
- Do not add cursor pagination in v1.
- Do not change document indexing, chunking, embeddings, or dataset import semantics.
- Do not add folder hierarchy beyond the existing folder model.

## Implementation Summary
- Added `DatasetListResponse` and `KnowledgeDocumentListResponse` schemas.
- Added shared dataset/document filter helpers in services.
- Added `count_datasets()` and `count_documents()` using the same filters as the list queries.
- Updated dataset and knowledge list routes to return envelope metadata.
- Updated frontend response types and state for dataset/document totals and `has_next`.
- Updated dataset and knowledge panels to show `shown of total` and use backend pagination state.
- Updated focused backend tests to assert totals, offsets, limits, `has_next`, search, unfiled, and folder filters.

## Validation
- Backend: `uv run pytest -s -q tests/test_datasets.py tests/test_knowledge_documents.py`
- Backend lint: `uv run ruff check app tests/test_datasets.py tests/test_knowledge_documents.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This changes the list API contract for datasets and knowledge documents; in-repo callers are updated, but any external client must now read `items`.
- The frontend still uses folder-count summaries for folder sidebar counts and server totals for the active filtered view. That is intentional: sidebar counts describe folder inventory, while list totals describe the current folder/search query.
- Selection behavior should be checked visually after page and folder changes, especially when a selected resource is no longer in the current folder or search result.

## Human Review Checklist
- Confirm dataset and knowledge libraries show accurate `shown of total` values.
- Confirm search results show totals for matching resources, not stale folder totals.
- Confirm Next is enabled only when the backend reports more records.
- Confirm folder panels remain useful when there are many imports or uploaded documents.
- Confirm delete and move controls are still visible for resources when permissions allow them.

## Interview Notes
This ticket demonstrates production API hygiene for admin/resource lists. The backend owns filtered counts and continuation state, while the frontend stays bounded and folder-scoped. That is important for local-first v1 and also maps cleanly to future scale, where resource libraries may contain thousands of imported datasets or knowledge documents.
