# Evaluation Run Folder Management

## Goal
Keep frontend surfaces that can grow with many named resources manageable by organizing evaluation run history into folders, reusing the existing workspace resource-folder system.

## Context
Knowledge documents and datasets already support `ResourceFolder` organization. Evaluation runs are another growing resource list with named runs, archive state, status filters, and detail inspection, but they remain flat. The user explicitly requested that frontend fields/lists that grow with many file or run names should be managed in folders.

## Requirements
- Extend resource folders to support `evaluation_run`.
- Add `folder_id` to evaluation runs.
- Allow evaluation runs to be created in a selected folder.
- Allow folder-scoped evaluation run listing.
- Allow authorized users to move evaluation runs between folders.
- Keep archive behavior separate from folder organization.
- Keep workspace isolation and existing permission checks.
- Update the evaluation UI so run history is folder-managed rather than a single flat growing list.

## Non-goals
- Do not redesign evaluation scoring.
- Do not add external file storage.
- Do not change knowledge/document folder behavior.
- Do not implement nested-folder browsing beyond the existing folder model.

## Design Plan
- Add `EvaluationRun.folder_id` nullable FK to `resource_folders.id`.
- Extend `VALID_RESOURCE_TYPES` and folder non-empty checks for `evaluation_run`.
- Add schema fields for evaluation run folder assignment and move requests.
- Add `folder_id` query filtering to `GET /evaluations`.
- Add `PATCH /evaluations/{evaluation_id}/folder`.
- Update frontend evaluation state with selected folder, run target folder, and folder panel.
- Reuse existing `ResourceFolderPanel`, `FolderPicker`, `filterByFolder`, and folder permissions.

## Test Plan
- Backend tests for creating an evaluation run in a folder, listing by folder, moving folders, invalid folder rejection, and workspace isolation.
- Frontend TypeScript/build validation.

## Risks
- Accidentally letting evaluation runs use dataset/document folders.
- Hiding archived evaluation runs unexpectedly when folder filtering is active.
- Permission drift between folder management and evaluation run archiving.

## Acceptance Criteria
- Evaluation runs can be organized by folder from the frontend.
- Backend enforces workspace-scoped folder assignment.
- Existing evaluation archive and detail views still work.
- Tests pass.

## Human Review Checklist
- Confirm the evaluation board no longer behaves like an unbounded flat list.
- Confirm folder labels and target folder controls are understandable.
- Confirm destructive archive controls still require owner permission.

## Interview Notes
This demonstrates resource lifecycle thinking: as operational artifacts grow, the app adds backend-enforced organization and permissions rather than only frontend search/limits.
