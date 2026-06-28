# Resource Lifecycle And Folder Audit

## Goal
Verify that user-created/uploaded resources have complete lifecycle controls: create/import/upload, inspect/edit where applicable, move into folders when lists can grow, and delete/archive when the current user has sufficient permission.

## Findings

| Resource area | Backend create/upload | Backend edit/move | Backend delete/archive | Frontend scalable organization | Permission model | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Knowledge documents | `POST /knowledge-documents` | `POST /knowledge-documents/{id}/reindex`, `PATCH /folder` | `DELETE /knowledge-documents/{id}` | Knowledge folder panel, folder-scoped library, search, move select, delete button | Members can upload/read/reindex; owners can move/delete/folders | Complete |
| Datasets/imports | `POST /datasets/import` | `PATCH /datasets/{id}/folder`, label editing on examples | `DELETE /datasets/{id}` | Dataset folder panel, folder-scoped library, search, move select, delete button | Members can import/read/label; owners can move/delete/folders | Complete |
| Resource folders | `POST /resource-folders` | `PATCH /resource-folders/{id}` | `DELETE /resource-folders/{id}` when empty | Dedicated folder panel for dataset and knowledge libraries | Owner-only create/rename/delete | Complete |
| Agents | `POST /agents` | `PATCH /agents/{id}` | `DELETE /agents/{id}` archives | Agent selector and run history; not a filename/file-list workflow | Owner-only archive; workspace-scoped read/run | Complete for v1 |
| Evaluation runs | `POST /evaluations` | Not edited after execution | `DELETE /evaluations/{id}` archives | Search/status/archive filter | Owner-only archive | Complete for v1 |
| Prompt templates | `POST /prompt-templates` | activate version | `DELETE /prompt-templates/{id}` archives | Grouped by prompt name, language, archive toggle | Owner-only create/activate/archive | Complete for v1 |
| Model configs | `POST /model-configs` | activate route | `DELETE /model-configs/{id}` archives | Grouped by purpose, archive toggle | Owner-only create/activate/archive | Complete for v1 |

## Evidence
- Backend route audit confirmed upload/import routes for knowledge documents and datasets have matching owner-only delete routes.
- `backend/tests/test_resource_folders.py` covers owner create/filter/move/delete, non-empty folder protection, member denial, and cross-workspace folder rejection.
- `backend/tests/test_knowledge_documents.py` covers document deletion cleanup and workspace scoping.
- Frontend `DatasetsPanel` and `DocumentsPanel` already use folder panels, folder-scoped lists, search, move controls, and delete controls.
- E2E smoke now asserts both dataset and knowledge libraries expose folder move and delete controls without breaking input focus on folder/review fields.

## Residual Risks
- V1 permissions are workspace-role based, not per-resource owner based. That is acceptable for the current small-team local tool, but should be revisited before adding custom enterprise roles.
- Folder hierarchy exists in the backend through `parent_folder_id`, but the current frontend presents a flat folder list. Keep it flat until users need nested folders; flat folders are faster and clearer for v1.
- Dataset and knowledge upload/edit are member-accessible while destructive cleanup is owner-only. This matches collaboration needs but should be explained in the README/interview notes.

## Acceptance Criteria
- Every upload/import surface has a corresponding delete/archive lifecycle path.
- Growing file/resource lists are folder-scoped or grouped before they become unbounded flat lists.
- Destructive actions remain permission-gated and covered by tests.
- Future tickets must not add upload/create surfaces without adding lifecycle controls in the same ticket.

## Verification
- `cd backend && uv run pytest -s -q tests/test_resource_folders.py tests/test_knowledge_documents.py` - 16 passed
- `cd frontend && npm test -- --run` - typecheck passed
- `make frontend-e2e-docker` - 1 passed

