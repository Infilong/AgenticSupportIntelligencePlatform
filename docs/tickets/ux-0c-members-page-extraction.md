# UX-0C: Extract Members Panel to MembersPage Page Component

## Goal
Continue frontend architecture cleanup by extracting the in-file `MembersPanel` into `frontend/src/pages/MembersPage.tsx` and wiring it through existing navigation/state handlers without behavior change.

## Context
This ticket is part of UX-0 (frontend architecture cleanup). The monolithic `AppShell.tsx` still exceeded 9k lines before extraction and mixed rendering and orchestration.

## Requirements
- Keep existing members UI behavior and permissions intact.
- Keep action handlers in `App` state ownership and pass required callbacks/state as props.
- Replace `return MembersPanel()` in `renderActiveTab` with `<MembersPage ... />`.
- Remove `MembersPanel()` function from `AppShell.tsx`.
- Keep "members" tab navigation and "Open audit trail" action routed via parent `goToTab`.

## Files to change
- `frontend/src/pages/MembersPage.tsx` (new)
- `frontend/src/app/AppShell.tsx`

## Risks
- Callback and prop typing mismatch for async handlers.
- Behavior drift if `TabShortcut` semantics changed incorrectly.
- Missing memoized callback identity changes causing unnecessary rerenders (acceptable in this stage).

# Human review checklist
- Confirm `MembersPage` render is equivalent to old in-place panel.
- Confirm member add/edit/remove actions remain wired to backend calls.
- Confirm refresh actions still call the same runAction path.
- Confirm audit trail action on members page navigates to audit tab.

## Validation
- `npm run build`
- `npm run test -- --run --watch=false`

