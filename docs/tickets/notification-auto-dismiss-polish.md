# Notification Auto-Dismiss Polish

## Goal
Make temporary frontend notifications disappear consistently and gradually instead of staying on screen or vanishing abruptly.

## Context
The global `Status` component is used for app-level notice and error messages. Before this ticket, success notices auto-cleared after a fixed timeout, but they disappeared instantly and error messages could remain until another action replaced them.

## Changes
- Added shared notification timing constants in `frontend/src/app/AppShell.tsx`.
- Applied the same visible duration and fade duration to success notices and error notifications.
- Added a `dismissing` state so notifications fade before being removed.
- Updated the existing status CSS to fade opacity and move slightly upward during dismissal.
- Added a focused Playwright regression test for refresh success and validation error notification dismissal.

## Validation
- `npm --prefix frontend run typecheck` passed.
- `npm --prefix frontend run build` passed.
- `API_URL=http://127.0.0.1:8000 npm --prefix frontend run test:e2e -- --project=chromium frontend/tests/e2e/notification-toast.spec.ts` could not run because WSL Chromium is missing `libnspr4.so`.
- Docker frontend/backend were rebuilt and checked.

## Manual Review Checklist
- Trigger `Refresh` and confirm `Workspace data refreshed` appears, fades, and disappears.
- Trigger a form validation error, such as creating a blank workspace, and confirm it uses the same fade timing.
- Confirm the notification does not block clicking controls behind it.

## Risks
- Auto-dismissing errors means long error text may disappear before a slow reader finishes. Current copy is short; if future errors become detailed, use inline persistent error panels for those instead of the global temporary notification.
