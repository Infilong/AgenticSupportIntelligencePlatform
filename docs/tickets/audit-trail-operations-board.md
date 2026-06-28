# Audit Trail Operations Board

## Goal
Turn the audit trail from a raw recent-event dump into an operator-friendly board that supports search, filtering, and bounded rendering.

## Context
The backend audit API is already workspace-scoped and limited to 100 recent events. The frontend still rendered every loaded event with no search or impact filters, which makes admin review harder as agents, prompts, models, documents, and reviews generate more audit records.

## Requirements
- Add audit search across action, resource type, resource id, actor id, and metadata.
- Add filters for impact level and actor type.
- Render a bounded number of matching audit events.
- Show clear loaded/matching/shown counts.
- Preserve metadata inspection through collapsed details.
- Do not change backend audit semantics in this ticket.

## Non-goals
- Do not add backend pagination or export.
- Do not change audit event schema.
- Do not hide high-impact events from metrics.

## Test Plan
- Run frontend production build.
- Run `git diff --check`.

## Human Review Checklist
- Confirm admins can find delete/archive/resolve events quickly.
- Confirm metadata remains inspectable but not visually dominant.
- Confirm empty filtered states are understandable.

## Interview Notes
This shows operational accountability: audit logs are not just stored for compliance, they are searchable evidence that admins can use during incident review, permission checks, and AI workflow governance.
