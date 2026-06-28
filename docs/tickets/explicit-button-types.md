# Explicit Button Types

## Goal
Reduce confusing form behavior by making every frontend button declare whether it is a submit action or a non-submit UI action.

## Context
The app is a form-heavy admin/developer console. Native HTML buttons default to `type=submit`, which can accidentally submit a nearby form when the button is meant to navigate, refresh, select, activate, archive, or open a detail view. This kind of issue can look like page jumps, lost focus, or unexpected state changes.

## Requirements
- Every `<button>` in `frontend/src/App.tsx` must have an explicit `type`.
- True form actions should use `type=submit`.
- Navigation, filters, segmented controls, row actions, archive/activate actions, and trace loaders should use `type=button`.
- Do not change backend behavior or form handlers.

## Non-goals
- Do not redesign page layouts.
- Do not change validation or API payloads.
- Do not add browser automation in this ticket.

## Implementation
- Added `type=submit` to actual form submit buttons.
- Added `type=button` to action/navigation buttons with click handlers.
- Verified with a full JSX button-tag scan that no button remains without an explicit type.

## Validation
- Full-tag audit script reported `MISSING_COUNT=0` for buttons without explicit `type`.
- `cd frontend && npm run build` passed.
- Browser QA was not rerun because WSL Playwright Chromium remains blocked by the missing `libnspr4.so` dependency and sudo requires a password.

## Human Review Checklist
- Confirm forms still submit through their primary action buttons.
- Confirm navigation/action buttons no longer cause unexpected form submits.
- Confirm typing in form fields and clicking nearby controls does not jump the page.

## Interview Notes
This ticket is a small but production-relevant UI stability fix. Professional admin consoles avoid ambiguous form controls because accidental submits damage trust and make debugging user reports harder.
