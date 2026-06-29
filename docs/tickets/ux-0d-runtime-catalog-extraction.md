# UX-0D: Extract Tools and Audit Panels to Dedicated Pages

## Goal
Move inline `ToolsPanel` and `AuditPanel` rendering from `AppShell.tsx` into dedicated page components and keep UI behavior equivalent.

## Context
This continues the frontend architecture cleanup started in earlier UX tickets (`UX-0A` AppShell cleanup, `UX-0B` tasks extraction, `UX-0C` members extraction).

## Requirements
- Create `frontend/src/pages/ToolsPage.tsx` and move the `ToolsPanel` UI into it.
- Keep tool catalog filtering, pagination, draft edit, and trace navigation behaviors intact.
- Maintain type-safety for tool models, schema/call detail rendering, and shared callbacks.
- Ensure `AppShell.tsx` no longer inlines the full tool panel rendering.
- Keep existing `AuditPage` extraction boundaries consistent with prior internal conventions.

## Acceptance Criteria
- `npm --prefix frontend run build` passes.
- `ToolsPanel` block is removed from `AppShell.tsx` and replaced with `<ToolsPage />`.
- `AuditPage` can still render and navigate via existing props.
- Build-time type compatibility for callbacks and payload types is resolved.

## Files changed
- `frontend/src/app/AppShell.tsx`
- `frontend/src/pages/ToolsPage.tsx`
- `frontend/src/pages/AuditPage.tsx`

## Risks
- Callback signature drift when moving large inline functions.
- Type mismatch between local tool payload aliases and global catalog types.
- Runtime safety when rendering `safeJson` on non-string tool-call payloads.

## Human Review Checklist
- Confirm Tool tab still shows: totals, filters, pagination, config save flow, and trace links.
- Confirm error/failure path still surfaces on tool rows.
- Confirm no regression in open-trace action and guardrail/attention links.
- Confirm `npm run build` passes after type migration.

## Notes
- `AuditPage.tsx` is now fully page-owned but this ticket focuses on structural extraction and build correctness.
