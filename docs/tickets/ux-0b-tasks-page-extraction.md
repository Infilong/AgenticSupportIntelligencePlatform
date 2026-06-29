# UX-0B: Extract Tasks Panel to TasksPage

## Goal
Extract the monolithic `tasks` workspace panel from `AppShell.tsx` into a dedicated page module while preserving behavior and permission-aware navigation.

## Context
This ticket continues the frontend architecture-cleanup sequence. After `UX-0A` separated the shell, this ticket begins page-level decomposition by isolating task/attention queue UI into its own component.

## Requirements
- Create `frontend/src/pages/TasksPage.tsx` with a dedicated task queue UI.
- Introduce shared UI primitives in `frontend/src/app/shared/Primitives.tsx` (`Badge`, `Metric`, `EmptyState`).
- Keep `frontend/src/App.tsx` as a thin shell entrypoint.
- Move rendering logic for `activeTab === "tasks"` from `AppShell.tsx` to `TasksPage`.
- Keep navigation actions (`goToTab`, `openAttentionItem`) and data flow behavior intact.
- Preserve review queue semantics:
  - summary cards
  - critical/warning/info grouping
  - next-task CTA
  - action button to corresponding tab/target

## Acceptance Criteria
- `npm run build` passes in `frontend/` (TypeScript + Vite build).
- `AppShell.tsx` no longer contains inline task list rendering.
- `App.tsx` remains minimal and re-exports shell.
- Attention items still navigate to correct targets.

## Files changed
- `frontend/src/App.tsx`
- `frontend/src/app/AppShell.tsx`
- `frontend/src/app/shared/Primitives.tsx`
- `frontend/src/pages/TasksPage.tsx`

## Risks
- Callback typing mismatch between local task row type and global `AttentionItem`.
- Regressions from moving code out of a giant file without end-to-end interaction checks.
- Premature extraction without shared helper extraction.

## Human Review Checklist
- Confirm task queue still appears under the Tasks tab.
- Confirm clicking "Open <tab>" opens matching route.
- Confirm critical/warning items keep their visual priorities.
- Confirm no behavior regression in the attention queue interactions.

## Notes
- This is a structural step only and prepares for further component extraction.
