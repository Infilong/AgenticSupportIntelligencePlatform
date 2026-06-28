# Review Queue Workflow Redesign

## Goal
Make the Human Review page understandable as an operations queue instead of a dense debug view. A reviewer should immediately know what is waiting, why it was blocked, what evidence exists, and what action is required.

## Implemented Changes
- Reframed the page as "Resolve blocked agent runs" with a clear operator task card.
- Added queue summary metrics for pending, assigned, unassigned, critical, evidence, and model/budget cases.
- Replaced the pending review card with numbered sections:
  1. customer request
  2. why it stopped
  3. classification
  4. evidence
  5. proposed answer
  6. resolution
- Changed no-draft review defaults from `rejected` to `edited`, so the human-approved answer box is usable immediately when the model refused or could not draft.
- Clarified the decision labels: approve proposed answer, send human-edited answer, or reject unsupported run.
- Cleaned duplicated Review CSS and added a single responsive layout block.
- Kept trace inspection, claim/release, owner badges, and resolved history available for admin/developer workflows.

## Verification
- `npm run test` -> passed (`tsc --noEmit`).
- `npm run build` -> passed (`tsc -b && vite build`).

## Human Review Notes
Manually verify in the browser:
- A pending review with no proposed answer opens with `Send human-edited answer` selected.
- Typing in `Human-approved answer` and `Reviewer note` keeps focus in the field.
- The page does not jump to the top while typing.
- `Inspect trace` takes the reviewer to the exact graph run.
- Resolved review history shows the stored answer and finalization trace link.

## Remaining Risk
This ticket improves the Review UI and default decision behavior. If focus loss still appears in browser, the next ticket should extract large nested panels into stable top-level React components and add a browser-level regression test for text input focus.
