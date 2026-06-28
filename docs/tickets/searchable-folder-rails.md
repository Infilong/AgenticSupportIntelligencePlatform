# Searchable Folder Rails For Growing Resource Libraries

## Goal
Keep folder-managed upload/import resources usable as folder counts grow. Dataset and knowledge libraries already use folders, but the folder rail itself must not become another unbounded list when a workspace accumulates many folders or file groups.

## Context
User feedback: all frontend areas that can grow with more file names should be managed in folders, otherwise the page becomes larger and harder to use. Previous tickets added folders, search, move, delete, and owner-gated lifecycle controls for datasets and knowledge documents. This ticket tightens the folder rail behavior itself.

## Requirements
- Keep existing dataset and knowledge folder APIs unchanged.
- Add folder search to each folder rail.
- Keep folder search state separate for dataset folders and knowledge folders.
- Bound the displayed folder rows so a large folder list does not stretch the panel.
- Preserve All folders and Unfiled shortcuts.
- Keep create, rename, delete, and selected-folder behavior intact.
- Add browser coverage proving folder search fields keep focus while typing.

## Non-goals
- No nested folder tree UI.
- No pagination or backend query changes.
- No bulk move/delete.
- No new upload surfaces.

## Audit Result
- Knowledge documents: create/upload, edit/reindex, move, delete, folder assignment, and chunk inspection already exist.
- Datasets: import, label editing, move, delete, folder assignment, and bounded example inspection already exist.
- Resource folders: create, rename, delete-empty, and owner-only permissions already exist.
- Remaining issue: the folder rail needed search/bounds to stay usable when folder names grow.

## Implementation Notes
- Added `MAX_VISIBLE_FOLDERS`.
- Added `folderSearches` state keyed by resource type.
- Added folder search input inside `ResourceFolderPanel`.
- Filtered and capped displayed folder rows while preserving All/Unfiled.
- Added an empty state for folder search misses and a note when matching folders are hidden by the cap.
- Extended the Docker Playwright smoke path to create real dataset and knowledge folders and type into both folder search inputs.

## Verification
- `cd frontend && npm test -- --run` passed.
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt and restarted the composed frontend/API stack.
- First `make frontend-e2e-docker` run failed because the test matched the folder row, Rename button, and Delete button by the same folder name; the product UI was working, and the test locator was made more specific.
- Final `make frontend-e2e-docker` passed, including Data folder search focus, Knowledge folder search focus, upload/import resource controls, Tools search focus, Guardrail search focus, trace navigation, and human-review editor focus.

## Human Review Checklist
- Confirm Data and Knowledge folder rails feel usable with many folders.
- Confirm folder search does not change the selected folder unless the user clicks a folder.
- Confirm move/delete controls still appear only for users with enough permission.
- Confirm folder search fields do not cause the page to jump or lose focus while typing.
