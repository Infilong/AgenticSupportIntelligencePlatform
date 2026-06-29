# Folder Picker Bounded Disclosure

## Goal
Keep file/document/resource organization controls compact as a workspace accumulates many folders and long resource names.

## Context
The app already organizes datasets, knowledge documents, agents, and evaluation runs with `ResourceFolder` records. The remaining UX issue was that some target-folder fields rendered the searchable folder list inline inside forms, so the form could grow as folder options grew.

## Requirements
- Folder target controls must not expand forms by default.
- Users must still see the current target folder clearly.
- Users must be able to open the picker, search folders, choose Unfiled, and choose a matching folder.
- Long selected folder names must not stretch the layout.
- The picker must stay bounded to the existing folder result limit and scroll behavior.

## Non-goals
- Do not add a new folder hierarchy model.
- Do not change backend folder APIs.
- Do not change dataset/document/evaluation permissions.
- Do not replace resource pagination.

## Design Plan
- Update the reusable `FolderPicker` component so non-compact target fields render as a disclosure control.
- Keep compact move controls unchanged in behavior.
- Add CSS to truncate long selected folder labels and keep the options list scroll-bounded.
- Extend the browser smoke test to prove Data, Knowledge, and Evaluation target folder fields are collapsed until opened.

## Files Changed
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/tests/e2e/review-ux-smoke.spec.ts`
- `docs/tickets/folder-picker-bounded-disclosure.md`

## Test Plan
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`
- Rebuild Docker API/frontend and run `make frontend-e2e-docker`.

## Acceptance Criteria
- Target folder fields do not show the full option list until opened.
- Search remains available after opening the picker.
- Long selected folder names truncate instead of resizing the form.
- Existing compact move controls still work.
- Browser smoke covers collapsed/open folder picker behavior.

## Risks
- Disclosure semantics may affect Playwright locators or keyboard interaction.
- Hiding options by default could make the target folder control less obvious, so the summary must show label, selected folder, and availability note.

## Human Review Checklist
- Open Data, Knowledge, and Evaluations forms and confirm folder target controls do not enlarge the form.
- Open each target picker and confirm search/options are visible.
- Check long folder names visually on desktop and narrow widths.
- Confirm move controls on existing resources still open normally.

## Interview Notes
This is a small UI systems decision: resource lists are backend-paginated and folder-scoped, while form controls use bounded disclosure pickers so operational screens stay stable as the tenant grows.
