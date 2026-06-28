# Audit Log Total Count Envelope

## Goal
Make audit-log pagination truthful for workspace administrators by returning backend-owned total metadata instead of bare arrays. Audit review should show how many matching events exist and should disable Next from backend `has_next`, not from page-size inference.

## Context
Audit logs are governance evidence for a professional AI platform. The previous backend pagination ticket added `search`, `actor`, `impact`, `limit`, and `offset`, but the API still returned a bare list and the UI guessed whether another page existed. That is acceptable for a demo, but weak for an admin console where operators need reliable navigation and counts.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/audit-logs` to return `items`, `total`, `limit`, `offset`, and `has_next`.
- Keep all search, actor, impact, limit, and offset behavior.
- Count only rows from the selected workspace and active filters.
- Update the Audit page to show matching totals and use backend `has_next`.
- Keep page-derived side metrics explicitly labeled as loaded-page metrics.
- Update tests to prove totals, filters, offsets, and workspace isolation.

## Non-goals
- Do not make audit logs deletable; they remain governance evidence.
- Do not add read-event audit logging in this ticket.
- Do not replace offset pagination with cursor pagination in v1.

## Implementation Summary
- Added `AuditLogListResponse`.
- Extracted shared audit filter construction and added `AuditLogService.count_logs()`.
- Updated the audit route to return a paginated envelope.
- Updated the frontend Audit page to consume `items`, `total`, and `has_next`.
- Added state clearing so audit totals do not linger when permissions/workspaces change.
- Updated tests for metadata and workspace-scoped filtered counts.

## Validation
- Backend: `uv run pytest -s -q tests/test_audit_logs.py`
- Backend lint: `uv run ruff check app tests/test_audit_logs.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This is an API contract change for audit-log list callers. Current in-repo callers are updated; external clients must read `items`.
- Impact filtering still uses action-name fragments. That limitation existed before this ticket and should be documented as a heuristic until audit events store explicit severity.

## Human Review Checklist
- Confirm the Audit page now reads as an operations timeline with accurate matching totals.
- Confirm side metrics clearly describe loaded-page counts, not global counts.
- Confirm this envelope pattern should continue to prompt/model histories and uploaded resource libraries.

## Interview Notes
This ticket shows governance-console thinking: audit logs are not just a rendered list, they are operational evidence. The backend owns workspace-scoped filtered totals, while the UI remains bounded and honest about what is page-local versus global.
