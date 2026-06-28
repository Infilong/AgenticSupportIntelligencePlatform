# Audit Log Backend Pagination

## Goal
Move the Audit operations timeline from a local filter over the latest fixed batch into a backend-filtered, paginated admin console surface.

## Context
Audit logs grow on every meaningful platform action: workspace settings, member changes, resource lifecycle, prompt/model changes, agent runs, review decisions, and evaluation cleanup. The previous UI loaded the latest 100 events and filtered locally. That made the page usable for a small demo, but it could hide older matching events and gave admins weak evidence during incident review.

## Requirements
- Add backend query support for audit `search`, `actor`, `impact`, `limit`, and `offset`.
- Keep audit logs workspace-scoped and permission-gated by `audit:read`.
- Preserve the existing audit response schema.
- Mirror the frontend impact mapping on the backend: deleted/activated/resolved are high impact; reindexed/updated/created are medium impact; everything else is low.
- Change the Audit page to load one backend-filtered page.
- Reset to page one when search, impact, or actor filters change.
- Add Previous/Next controls.

## Non-goals
- Do not add a total-count endpoint in this ticket.
- Do not change the audit event schema or write semantics.
- Do not implement event sourcing or immutable external audit storage.
- Do not add read-event auditing.

## Design Plan
- Extend `AuditLogService.list_logs()` with search, actor, impact, offset, and limit filters.
- Extend `GET /api/v1/workspaces/{workspace_id}/audit-logs` query params with typed filters.
- Add tests covering user/system actor filters, impact filters, search, offset pagination, and workspace scoping.
- Add `auditPage` and `auditLogListParams()` in the frontend.
- Replace local Audit timeline filtering with backend-loaded results.

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_audit_logs.py`
- `cd backend && uv run ruff check .`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Audit API filters before pagination.
- Audit UI no longer claims it filters only the latest 100 events.
- Search, impact, actor, and page changes load backend-filtered audit events.
- Existing reviewer/browser smoke checks still pass, including audit search focus stability.

## Risks
- Page-level metrics now summarize the loaded page, not the total matching audit corpus.
- Without a total-count endpoint, a full page enables Next even if the next page is empty.
- Backend impact mapping duplicates the frontend mapping and should be kept in sync if audit severity rules become configurable.

## Human Review Checklist
- Confirm the Audit page clearly communicates that it is showing a backend-loaded page.
- Confirm filter changes do not make the page jump or input focus fail.
- Confirm admins can still inspect metadata and resource identifiers.
- Confirm non-admin roles cannot access the Audit tab/API.

## Interview Notes
This ticket turns audit logs into operational evidence instead of a shallow UI dump. It shows backend-owned filtering, workspace-scoped access, pagination, and an honest discussion of total-count and severity-classification tradeoffs.
