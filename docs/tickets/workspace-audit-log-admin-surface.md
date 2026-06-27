# Workspace Audit Log Admin Surface

## Goal
Make workspace operations more accountable by adding a visible audit trail for important admin and AI workflow actions.

## Audit Finding
The project documentation described audit logs, but the product did not expose an implemented audit model, API route, or UI page. That weakened the professional AI platform story because admins could not answer who changed model settings, prompts, documents, agents, or human review decisions.

## Changes Made
- Added `AuditLog` persistence with workspace scope, actor user, action, resource type, resource id, metadata JSON, and timestamp.
- Added workspace-scoped audit log API:
  - `GET /api/v1/workspaces/{workspace_id}/audit-logs`
- Recorded audit events for key operational actions:
  - agent create/update/run completion
  - knowledge document upload/reindex/delete
  - prompt template version create/activate
  - model config create/activate
  - human review resolution
- Added an `Audit logs` frontend tab and developer toolbox shortcut.
- Added a workspace status metric for audit events.
- Added backend tests for event creation, metadata recording, and workspace isolation.
- Updated known limitations to distinguish implemented audit coverage from future event-sourcing or full read auditing.

## Verification
Completed for this ticket:
- `uv run pytest -s tests/test_audit_logs.py` -> 2 passed
- `uv run ruff check .` -> passed
- `uv run pytest -s` -> 85 passed
- `npm run build` -> passed
- `npm run test` -> passed

Runtime smoke:
- `docker compose up -d --build api frontend` -> services rebuilt and started
- `uv run alembic upgrade head` -> upgraded `0008_evaluation` to `0009_audit_logs`
- Live API smoke created a workspace/agent and returned `agent.created` from `/audit-logs`
- `curl -I http://127.0.0.1:5173` -> 200 OK

## Remaining Risks
- Audit coverage is focused on high-value admin/workflow actions, not every read or low-risk operation.
- Audit logs are mutable database rows rather than append-only tamper-evident events.
- Role-based admin permissions are not implemented yet; workspace membership remains the authorization boundary.
- Metadata is intentionally concise and must not include secrets, raw documents, or PII.

## Next Recommended Ticket
Harden the LangGraph workflow into a more visibly stateful runtime: add explicit checkpoint/resume semantics, graph execution metadata, and UI affordances that show graph state transitions rather than only persisted backend rows.
