# Tool Execution History Detail

## Goal
Make tools first-class operational objects by showing backend-backed execution and error history directly in the Tools page, not only aggregate counts and trace links.

## Files Changed
Expected files:
- `backend/app/services/tool_service.py`
- `backend/app/schemas/tool.py`
- `backend/app/api/v1/tools.py`
- `backend/tests/test_tools.py`
- `frontend/src/App.tsx`

## Design Reasoning
The current tool catalog already exposes runtime definitions, workspace defaults, usage totals, and recent execution summaries. The missing professional-console behavior is inspection: developers should see which graph step/run used a tool, what input/output was recorded, and why a failed call failed before jumping to the full trace.

This ticket enriches the existing `recent_calls` response instead of adding a separate model or broad new page. The list remains bounded to avoid large payloads.

## Backend/API Impact
- Extend recent tool call summaries with graph step name, graph run status/language/input context, input JSON, output JSON, and step error message.
- Keep workspace scoping through the existing `/workspaces/{workspace_id}/tools` route.
- No database migration required.

## Tests / Validation
- Add backend tests proving recent tool calls include run/step context, input/output JSON, and error detail for failed calls.
- Run backend `ruff` and focused tool tests.
- Run frontend build.

## Risks
- Tool catalog response becomes larger; bounded recent calls keep this acceptable for v1.
- Raw JSON should remain behind disclosure controls, not become the primary UI.
- Error details must stay workspace-scoped through existing route permissions.

## Manual Review Checklist
- In Tools, run a successful agent call and inspect recent execution context.
- Disable `search_documents`, run an agent, then confirm the failed tool call shows error context.
- Confirm the trace link still works from each execution row.

## Before / After Behavior
Before: Tools showed counts and short recent call summaries, with details only available after jumping to Trace.
After: Tools show run input, graph step, status, latency, error message, and expandable input/output evidence directly in the tool card.
