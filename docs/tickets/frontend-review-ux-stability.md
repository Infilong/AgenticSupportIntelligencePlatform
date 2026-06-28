# Frontend Review UX Stability

## Goal
Make the Human Review workflow easier to understand and fix frontend input stability issues reported during manual testing.

## User-Reported Problems Addressed
- Typing in some fields could cause focus loss or page jump behavior.
- Human Review was confusing because it showed resolved/no-proposed-answer states and did not make pending work obvious enough.
- Folder/file-heavy areas must stay organized instead of growing into unbounded flat lists.

## Changes
- Changed folder panel rendering from nested JSX component usage to direct render-helper calls.
  - This avoids remounting `ResourceFolderPanel` every time `App` state changes, which can drop focus after one character in folder name inputs.
- Removed duplicated dataset label dropdown options.
- Added `selectedReviewId` and a stable selected pending review flow.
- Reworked Human Review into:
  - queue summary metrics with clearer labels;
  - compact pending review queue;
  - one selected full review case and editor;
  - selected-case summary in the policy panel.
- Kept resolved review history below the active queue so old resolved items do not compete with pending review work.
- Added CSS for compact review queue rows, selected-case summary, and contained long text.
- Split trace/review CSS grid selectors so the Trace layout is not accidentally changed by Review-specific layout work.

## Folder Management Note
The document and dataset pages already use folder-scoped library panels, scoped search, move controls, and owner-only delete controls. This ticket preserves that pattern and fixes folder input focus stability by preventing nested component remounting.

## Validation
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.

## Manual Review Checklist
- In Knowledge and Datasets, type several characters into the new-folder field and confirm focus stays in the input.
- In Human Review, confirm pending cases appear in the compact queue and selecting a case opens the detailed editor.
- Type multiple characters into reviewer note and human-approved answer fields and confirm focus remains stable.
- Confirm resolved review history is visually separate from the active queue.

## Remaining Risk
Browser automation coverage was added later in `docs/tickets/browser-smoke-test-harness.md`. This original ticket was validated by TypeScript/build plus manual review; the follow-up Playwright smoke now covers folder typing and review editor typing once WSL browser system dependencies are installed.
