# Folder-Bounded Resource Lists

## Goal
Keep upload/edit resource pages usable as file and dataset counts grow by making large lists folder-scoped, search-first, and bounded in the frontend.

## Context
The backend already supports workspace-scoped resource folders, document/dataset move APIs, document/dataset delete APIs, and permission gates. The remaining UX risk was that a busy folder could still render every matching document or dataset in the page, making the console feel unstable as more files are uploaded.

## Requirements
- Keep knowledge documents and datasets organized through folder scope.
- Bound the number of visible documents/datasets inside the selected folder.
- Preserve search so users can narrow long lists before editing, moving, or deleting resources.
- Keep delete and move controls permission-aware.
- Do not add fake backend data or bypass existing folder APIs.

## Non-goals
- Do not add backend pagination in this ticket.
- Do not redesign the whole knowledge page.
- Do not change document indexing, retrieval, or chunking behavior.

## Implementation
- Added a shared `MAX_VISIBLE_RESOURCES` frontend limit.
- Dataset and document lists now render the first matching resources in the selected folder scope.
- Added clear notes when more matching resources exist, directing users to search before moving/deleting/editing in large workspaces.
- Reused existing folder panels, move APIs, delete APIs, and permission flags.

## Validation
- `cd frontend && npm run build` passed.
- `cd backend && uv run pytest -s -q tests/test_resource_folders.py tests/test_knowledge_documents.py` passed: 16 passed, 1 warning.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm the knowledge and dataset pages still make upload/edit/delete actions obvious.
- Confirm long document names wrap cleanly and do not stretch the layout.
- Confirm the user understands folders are the main way to manage uploaded files as the workspace grows.

## Interview Notes
This ticket shows pragmatic scale design: v1 stays local-first without backend pagination, but the UI avoids unbounded resource panels and already aligns with future paginated folder APIs.
