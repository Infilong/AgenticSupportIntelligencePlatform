# Resource Library Scale Audit and UI Follow-up

## Goal
Audit upload/import resource lifecycle coverage and improve the frontend so growing file/resource name lists stay organized by folders and searchable within the current folder.

## User Feedback
- Any user-uploaded/imported resource should also be editable, movable, or deletable when the user has enough permission.
- Frontend areas that can grow with many filenames/resources should not become long flat lists.
- File-heavy areas should be managed through folders before the app grows.

## Audit Result

| Surface | Create/upload/import | Edit/update | Folder support | Delete/archive | Permission enforcement | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knowledge documents | `POST /knowledge-documents` | reindex/edit via `POST /knowledge-documents/{id}/reindex` | create/list/delete folders, assign on upload, move later | owner-only `DELETE /knowledge-documents/{id}` | backend `require_workspace_owner` for destructive/move actions; tests cover member denial and workspace isolation | Covered |
| Datasets | `POST /datasets/import` | label editing for imported examples | create/list/delete folders, assign on import, move later | owner-only `DELETE /datasets/{id}` | backend `require_workspace_owner` for destructive/move actions; tests cover member denial and workspace isolation | Covered |
| Resource folders | `POST /resource-folders` | `PATCH /resource-folders/{id}` | shallow folder hierarchy in schema | owner-only delete when empty | backend rejects non-owner, non-empty, invalid type, and cross-workspace IDs | Covered |
| Prompt templates | create/update/activate templates | versioned prompt records | no folder support | no delete in v1 | workspace-scoped API | Not a file-upload surface; future archive may be useful |
| Model configs | create/update/activate configs | settings edit | no folder support | no delete in v1 | workspace-scoped API | Not a file-upload surface; future archive may be useful |
| Agents/tools/guardrails | runtime/admin resources | activation/archive or catalog views depending surface | no folder support | agent archive exists; tools/guardrails are runtime catalog views | workspace-scoped API | Not file uploads |

## Changes Made
- Added folder-local search to the Data dataset library.
- Added folder-local search to the Knowledge document library.
- Added clearer owner lifecycle notes next to the growing resource lists.
- Kept folder rails, scroll-bounded lists, and move/delete controls as the primary organization model.

## Current Design Decision
For v1 local-team scale, support two layers of organization:

1. Folder rail: groups documents/datasets by product, client, language, test purpose, or policy area.
2. Search within current folder: prevents long filename lists from becoming hard to scan.

Do not add pagination or a tree-heavy file manager yet. The current dataset/document counts are small-team oriented; pagination becomes a later ticket when API list sizes become large enough to require it.

## Verification Plan
- Frontend tests/build should pass.
- Backend lifecycle tests should continue to pass:
  - `test_resource_folders.py`
  - `test_knowledge_documents.py`
  - `test_datasets.py`
- Live UI should show folder rail plus search on Data and Knowledge pages.

## Risks and Follow-ups
- Dataset hard delete is acceptable for the local portfolio demo, but archive/restore would be safer for production teams.
- Prompt templates and model configs are not file uploads, but they may need archive controls when the settings surface grows.
- Nested folders exist at schema level but are not exposed in UI. Keep this out of v1 unless users need deeper hierarchy.
- Pagination is still postponed until resource counts justify it.


## Follow-up Implementation Record: Document Row Actions and Folder Targets

User feedback after the first folder pass: any upload/import surface must expose manipulation options, and fields that can grow with many file names should be folder-managed.

Additional frontend changes:
- Knowledge document rows now expose inline owner-gated move and delete controls, matching dataset rows.
- Selecting a dataset folder sets the import form target to that folder.
- Selecting a knowledge folder sets the upload form target when creating a new document.
- Data and Knowledge libraries now show both current folder scope and import/upload target so users understand where new resources will land.
- The browser smoke test now creates a real knowledge document through the backend and verifies its move/delete controls are visible.

Current audit conclusion:
- Upload/import file-like surfaces in v1 are Knowledge documents and Datasets.
- Both surfaces now support create/import, update where applicable, folder assignment, move, delete, workspace scoping, owner-only destructive actions, and audit logging.
- Prompt templates/model configs are growing admin records, not file uploads; future archive/delete controls should be handled in a separate settings-lifecycle ticket.

Validation:
- `cd frontend && npm run typecheck`: passed.
- `cd frontend && npm run build`: passed.
- `cd backend && uv run pytest -s -q tests/test_resource_folders.py`: 4 passed.
- `make frontend-e2e-docker`: passed.
