# Searchable Folder Pickers

## Goal
Replace growing folder dropdowns in the Data and Knowledge workflows with searchable folder pickers so uploaded resources remain manageable as folder count grows.

## Context
The backend already supports workspace-scoped resource folders, document/dataset move APIs, document/dataset delete APIs, and permission gates. The frontend had folder panels and bounded resource lists, but folder selection still used native `<select>` controls that become hard to use when a workspace has many folders.

## Requirements
- Replace folder dropdowns for dataset import, dataset move, document move, and knowledge document upload/edit target.
- Keep folder management permission-aware.
- Keep row-level move controls compact so resource lists remain scannable.
- Keep form-level target selection explicit for uploads and edits.
- Avoid fake backend behavior; use the existing move/upload/reindex APIs.

## Non-goals
- Do not add backend pagination in this ticket.
- Do not change folder permissions or database schema.
- Do not redesign the full Data or Knowledge pages.

## Implementation
- Added a reusable module-level `FolderPicker` component with local search state.
- Full picker is used for upload/import/edit target fields.
- Compact expandable picker is used in dataset/document row actions.
- Picker limits visible folder options to `MAX_VISIBLE_FOLDERS` and prompts search when there are more matches.
- Added CSS for full and compact picker states with wrapping long folder names.

## Validation
- `cd frontend && npm run build` passed.
- `cd backend && uv run pytest -s -q tests/test_resource_folders.py tests/test_knowledge_documents.py` passed: 16 passed, 1 warning.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm row-level move controls are compact enough for many documents/datasets.
- Confirm upload/edit target selection is more discoverable than the old dropdown.
- Confirm search input focus behaves normally while typing folder names.
- Confirm folder names with long text wrap instead of stretching the layout.

## Interview Notes
This ticket shows a pragmatic scale-aware frontend decision. The app does not pretend to implement enterprise pagination yet, but it avoids unbounded native dropdowns and keeps resource organization aligned with backend folder APIs and permission gates.
