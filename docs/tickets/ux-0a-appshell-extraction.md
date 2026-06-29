# UX-0A: App Shell Extraction

## Goal
Reduce `App.tsx` architectural risk by extracting the monolithic implementation into `app/AppShell.tsx` and making `App.tsx` a thin composition entrypoint.

## Context
This ticket executes the first frontend recovery step from the active objective (`frontend and backend polishment -> UX-0A`): remove the single giant file illusion at the entrypoint and establish a stable shell boundary for subsequent page/component splits.

## Requirements
- Preserve current behavior and routes.
- Remove most application logic from `frontend/src/App.tsx`.
- Keep all existing imports, handlers, and rendering behavior unchanged.
- Maintain backward compatibility with `main.tsx` imports.

## Plan
- Move current `frontend/src/App.tsx` to `frontend/src/app/AppShell.tsx`.
- Replace `frontend/src/App.tsx` with a minimal re-export entrypoint.
- Do not modify runtime logic, state, API calls, or UI output in this ticket.

## Files changed
- `frontend/src/App.tsx`
- `frontend/src/app/AppShell.tsx`
- `docs/tickets/ux-0a-appshell-extraction.md`

## Risk
- Any bundler or import path regression from the move.
- Unintentional export mismatch (`App` named export).

## Human Review Checklist
- Confirm `main.tsx` still renders `<App />` correctly.
- Confirm `frontend/src/App.tsx` contains only shell wiring.
- Confirm logic remains in `frontend/src/app/AppShell.tsx` and behavior appears unchanged on existing routes.

## Notes
This is intentionally a prerequisite ticket. It does not introduce routes, components, or new UI behavior.
