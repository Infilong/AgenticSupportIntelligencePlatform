# Resource Folder-First Management

## Goal
Make uploaded resources behave like manageable workspace assets, not one-way uploads. Knowledge documents and datasets must be organized by folders, searchable inside a folder scope, movable, deletable by owners, and protected from accidental folder deletion while resources remain inside.

## Context
The backend already exposes workspace-scoped resource folder, document move/delete, and dataset move/delete APIs. The frontend needed stronger folder-first affordances so large workspaces do not become flat lists of file names.

## Requirements
- Keep dataset and knowledge libraries folder-scoped.
- Show current folder scope and visible resource counts.
- Let owners rename folders from the UI.
- Keep folder deletion disabled when the folder contains resources.
- Preserve owner-only destructive controls and member read-only behavior.
- Ensure long resource and folder names wrap instead of expanding panels.

## Non-goals
- No bulk delete.
- No arbitrary drag-and-drop folder tree.
- No new storage backend.
- No cloud object storage.

## Design Plan
- Extend the existing `ResourceFolderPanel` with rename mode and clearer folder actions.
- Add folder scope banners to dataset and knowledge libraries.
- Add CSS for folder actions, scope banners, and long-name wrapping.
- Add backend tests for folder rename and non-empty folder delete conflicts.

## Test Plan
- Run resource folder tests.
- Run frontend tests and production build.
- Run full backend test suite if focused checks pass.
- Rebuild Docker frontend and smoke check API/frontend URLs.
- Attempt browser screenshot QA; currently blocked if WSL lacks Playwright Chromium system libraries.

## Acceptance Criteria
- Owners can rename folders.
- Non-empty folders cannot be deleted.
- Dataset and document lists clearly show current folder scope and counts.
- Long names remain contained in the panel layout.
- Existing workspace/RBAC tests remain green.

## Risks
- Folder controls can become too dense if every future resource type is added without grouping.
- Browser UX still needs visual QA with a larger seeded workspace.

## Human Review Checklist
- Confirm the Knowledge and Data tabs make upload, move, edit, and delete discoverable.
- Confirm member users can inspect resources but cannot rename folders or delete resources.
- Confirm long document names do not stretch the layout.

## Interview Notes
This ticket demonstrates lifecycle completeness: when a product lets users upload data, it also needs ownership, organization, update, delete, audit, and permission boundaries. Folder-first management keeps the local MVP honest while leaving room for future object storage or enterprise search.

## Validation Results
- `cd backend && uv run ruff check app tests/test_resource_folders.py`: passed.
- `cd backend && uv run pytest tests/test_resource_folders.py -q -s`: 4 passed.
- `cd backend && uv run pytest -q -s`: 117 passed, 1 Starlette/httpx deprecation warning.
- `cd frontend && npm run test -- --run`: passed TypeScript check.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.
- `docker compose up -d --build frontend`: rebuilt and restarted API/frontend.
- `curl http://127.0.0.1:8000/health`: returned ok.
- `curl http://127.0.0.1:5173`: returned frontend HTML.
- Browser screenshot QA attempted with Playwright, but Chromium launch is blocked by missing WSL library `libnspr4.so`.
