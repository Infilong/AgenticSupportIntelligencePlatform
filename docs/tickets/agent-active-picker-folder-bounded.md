# Agent Active Picker Folder-Bounded UX

## Goal
Replace the primary Active agent dropdown with a bounded, searchable, folder-scoped picker so the run path does not become a giant flat list as agent configs grow.

## Context
The user flagged that frontend fields which can grow with many file/resource names should be managed through folders. A fresh audit showed the upload-style resource libraries already have backend and frontend manipulation controls:

- Knowledge documents: upload, edit/reindex, move to folder, delete, backend folder/search/page listing.
- Datasets: import, move to folder, delete, backend folder/search/page listing.
- Agents: create, move to folder, archive, backend folder/search/page listing.
- Evaluation runs: run/upload JSONL cases, move to folder, archive, permanently delete archived runs, backend folder/search/status/page listing.

The remaining anti-scale UI in the main workflow was the Agent page hero control: it still used a native select for Active agent. Native selects are poor for long resource names and do not expose folder/search context.

## Requirements
- Remove the flat Active agent select from the hero area.
- Use the current agent folder and backend-paged agent list as the selection scope.
- Provide a search field before selection.
- Bound visible picker options with `MAX_VISIBLE_AGENT_PICKER_OPTIONS`.
- Keep long agent names wrapped inside the control instead of stretching the layout.
- Do not change backend permissions or schemas.
- Do not add fake resource folders for non-file operational histories.

## Implementation
- Added computed active-agent picker options from the current backend-loaded agent page.
- Preserved the selected agent in the picker when it is outside the current loaded page.
- Replaced the hero `<select>` with a searchable listbox-style picker.
- Added compact CSS for stable picker dimensions, bounded scrolling, and long-name wrapping.
- Updated browser smoke coverage to assert the picker search keeps focus and no native select remains in the active-agent picker.

## Permission And Data Integrity Notes
The ticket uses existing backend-backed agent list data. Folder filtering, search, pagination, move controls, and archive controls remain enforced by existing workspace permission APIs. No frontend-only permission shortcut was added.

## Validation Plan
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`
- `make frontend-e2e-docker`
- `git diff --check`

## Human Review Checklist
- Confirm the Active agent area is understandable without a dropdown.
- Confirm agent search stays focused while typing.
- Confirm long agent names wrap and do not stretch the hero panel.
- Confirm the Agent library still exposes folder, move, inspect, and pagination controls.
- Confirm uploadable resources still have matching edit/delete/move controls where permissions allow it.

## Interview Notes
This is a product-scale UI decision: professional internal platforms should not rely on flat dropdowns for growing workspace resources. Folder-scoped, searchable, paginated selectors keep the UI operable at 10 resources and at hundreds of resources without pretending the local v1 has enterprise-scale infrastructure.
