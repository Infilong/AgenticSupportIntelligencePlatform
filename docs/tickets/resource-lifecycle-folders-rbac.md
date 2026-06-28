# Resource Lifecycle, Folders, and Role-Gated Actions

## Goal
Add backend-supported resource organization and cleanup for the largest growing surfaces: Knowledge documents and Data datasets. Users with enough permission should be able to upload/import, organize, move, archive/delete, and inspect resources without flat lists growing indefinitely.

## Context
The current app supports knowledge document upload/edit/delete, but delete is only workspace-member gated. Dataset import has no delete/archive and no folder organization. The active product goal requires permission-aware controls, backend-enforced authorization, and data/tool organization that scales when many files or resources exist.

Relevant files:
- `backend/app/dependencies/workspace.py`
- `backend/app/models/workspace.py`
- `backend/app/models/knowledge.py`
- `backend/app/models/dataset.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/datasets.py`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`

## Requirements
- Add role-aware backend permission helpers for read/write/destructive actions.
- Use owner/admin-level permission for hard delete in v1. With current roles, `owner` is destructive-capable and `member` is non-destructive unless upgraded later.
- Add folder/collection organization for `knowledge_document` and `dataset` resources.
- Knowledge documents and datasets can be assigned to a folder on create/import and moved later.
- Frontend shows folder filters/tree for Knowledge and Data instead of only flat lists.
- Frontend exposes delete/archive controls only when backend role allows it.
- Backend enforces permissions even if frontend is bypassed.
- Audit logs record folder create/update/delete, resource move, dataset delete/archive, and knowledge delete.
- Tests prove owner allowed, member denied, cross-workspace denied, and folder filtering works.

## Non-goals
- Do not implement full enterprise RBAC/custom roles yet.
- Do not implement arbitrary nested drag-and-drop UI.
- Do not add a full tool registry or guardrail registry in this ticket.
- Do not hard delete resources that are referenced by graph runs unless cascade behavior is explicit and tested.
- Do not implement cloud storage or file binaries; current app still stores text content.

## Design Plan
Backend:
- Add `ResourceFolder` model with `workspace_id`, `resource_type`, `name`, `parent_folder_id`, `created_by_user_id`, timestamps.
- Add nullable `folder_id` to `knowledge_documents` and `datasets`.
- Add folder schemas and service methods.
- Add folder API routes under workspace scope.
- Extend knowledge upload/reindex/move/list with `folder_id` filtering.
- Extend dataset import/list with `folder_id`; add dataset delete or archive endpoint.
- Add role-aware dependencies. Start with current roles: `owner` can delete/manage folders; `member` can read and perform non-destructive actions where existing behavior requires it.

Frontend:
- Add a compact folder rail/filter to Data and Knowledge pages.
- Add folder create/rename/delete controls.
- Add folder selector to dataset import and knowledge document forms.
- Add move action for selected dataset/document.
- Add delete/archive action with confirmation and permission-aware disabled state.

## Files Likely To Change
- `backend/app/models/folder.py` or a suitable existing model module
- `backend/app/models/__init__.py`
- `backend/alembic/versions/*_resource_folders.py`
- `backend/app/schemas/folder.py`
- `backend/app/services/folder_service.py`
- `backend/app/dependencies/workspace.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/folders.py`
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/datasets.py`
- `backend/tests/test_resource_folders.py`
- `backend/tests/test_knowledge_documents.py`
- `backend/tests/test_datasets.py`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `docs/professional-platform-audit.md`

## Database Migrations
- Create `resource_folders` table.
- Add `folder_id` nullable FK to `knowledge_documents`.
- Add `folder_id` nullable FK to `datasets`.
- Add indexes for `(workspace_id, resource_type)`, `(workspace_id, parent_folder_id)`, `(workspace_id, folder_id)` on target tables.

## API Changes
- `GET /api/v1/workspaces/{workspace_id}/resource-folders?resource_type=...`
- `POST /api/v1/workspaces/{workspace_id}/resource-folders`
- `PATCH /api/v1/workspaces/{workspace_id}/resource-folders/{folder_id}`
- `DELETE /api/v1/workspaces/{workspace_id}/resource-folders/{folder_id}`
- `GET /knowledge-documents?folder_id=...`
- `POST /knowledge-documents` accepts `folder_id`
- `PATCH /knowledge-documents/{document_id}/folder`
- `GET /datasets?folder_id=...`
- `POST /datasets/import` accepts `folder_id`
- `DELETE /datasets/{dataset_id}` or `POST /datasets/{dataset_id}/archive`

## Test Plan
- Folder create/list/update/delete as owner.
- Non-member cannot access folders.
- Member cannot perform destructive folder or resource deletion.
- Cross-workspace folder IDs cannot be used during document upload or dataset import.
- Knowledge document list filters by folder.
- Dataset list filters by folder.
- Deleting a knowledge document still removes versions/chunks/embeddings and writes audit log.
- Deleting/archive dataset removes or hides examples/messages/labels according to final design and writes audit log.
- Frontend typecheck/build after UI changes.

## Acceptance Criteria
- Data and Knowledge pages no longer rely only on flat growing lists.
- Users can organize documents and datasets into workspace-scoped folders.
- Destructive actions are backend role-gated.
- Frontend controls reflect permission state and explain restricted actions.
- Tests cover permissions, cross-workspace isolation, and folder filtering.
- Audit logs capture lifecycle actions.

## Risks
- Hard-deleting datasets may remove evaluation-relevant examples; archive may be safer.
- Adding folders without search/pagination only partially solves large-list scale.
- Current role model is minimal; avoid overclaiming admin/developer/reviewer/viewer until backend supports them.
- Nested folders can create complexity; start with shallow folders unless strongly needed.

## Human Review Checklist
- Confirm owner/member behavior matches the desired local-team workflow.
- Confirm folder UI feels like organization, not another confusing form.
- Confirm delete/archive copy is clear and not accidental.
- Confirm backend tests prove frontend cannot bypass permission checks.

## Operating Notes
This is the next recommended implementation ticket after the IA cleanup. It directly addresses user feedback that uploaded/imported resources must be manipulable and organized before lists become too large.


## Implementation Record
Implemented resource lifecycle organization as a shallow folder model for datasets and knowledge documents.

Backend changes:
- Added `ResourceFolder` with workspace ownership, resource type, optional parent ID, and creator.
- Added nullable `folder_id` to `KnowledgeDocument` and `Dataset`.
- Added folder CRUD API with owner-only create/update/delete and member list access.
- Added folder validation to document upload/list/reindex/move and dataset import/list/move.
- Added owner-only delete endpoints for knowledge documents and datasets.
- Added audit records for folder, document, and dataset lifecycle actions.

Frontend changes:
- Added compact folder panels to Data and Knowledge pages.
- Added folder selectors during dataset import and knowledge document upload/edit.
- Added folder filtering, resource move controls, and delete controls.
- Kept growing resource lists inside bounded scroll areas so many filenames do not stretch the page.
- Disabled destructive controls for non-owners using current workspace ownership data.

Verification focus:
- Backend tests cover owner lifecycle, member denial, cross-workspace folder rejection, folder filtering, and reindex-to-unfiled behavior.
- Frontend validation should confirm folder panels, move/delete controls, and scrollable lists remain clear on desktop and mobile.

Known limitations:
- Folders are shallow in v1; nested folders are represented in the schema but not exposed in the UI.
- Dataset deletion is hard delete in v1; archive/restore is a future safer lifecycle ticket.
- Frontend owner detection currently uses `workspace.created_by_user_id`; a richer membership/role API should replace this when role management expands.
