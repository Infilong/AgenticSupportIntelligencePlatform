# Runtime Tool Catalog Page

Date: 2026-06-28

## Goal
Make tools a first-class product area instead of hiding tool execution inside individual traces. Developers should be able to inspect tool contracts, permissions, runtime usage, failures, and trace links from a dedicated Tools page.

## Context
The professional platform objective requires tool management as a first-class concept. The current app already persisted `ToolCall` rows during LangGraph runs, but there was no workspace-scoped API or navigation page for tools. A full configurable tool registry is still a future structural ticket, so this ticket intentionally implements a runtime-backed catalog using real backend definitions and persisted usage.

## Implementation
- Added `app/schemas/tool.py` with tool catalog, usage, and recent-call response models.
- Added `ToolService` with a runtime definition for the LangChain `search_documents` `StructuredTool`.
- Aggregated per-workspace tool usage from real `ToolCall` rows.
- Added `GET /api/v1/workspaces/{workspace_id}/tools`.
- Added focused tests proving tool usage is populated by a real agent run and isolated by workspace.
- Added Tools to the frontend navigation and readiness flow.
- Added a Tools page showing:
  - tool name, framework, description, enabled state
  - permissions
  - retry and timeout policy
  - input/output schemas behind details
  - total calls, failures, average latency, last used
  - recent executions linked back to graph traces

## Backend/API Impact
The new tools endpoint is read-only and workspace-scoped through `require_workspace_member`. It does not yet mutate tool configuration. The endpoint uses runtime definitions plus persisted `ToolCall` rows, so it is honest about what exists today.

## Validation
- `uv run ruff check .` passed.
- `uv run pytest tests/test_tools.py -q -s` passed: 2 tests.
- `uv run pytest -q -s` passed: 99 tests.
- `npm run test -- --run` passed.
- `npm run build` passed.

## Manual Review Checklist
- Open the Tools page from the sidebar.
- Confirm `search_documents` is visible before any tool calls.
- Run an agent with a knowledge document indexed.
- Confirm tool usage count and recent execution update.
- Click a recent execution and confirm it opens the related trace.
- Confirm another workspace does not see the first workspace's tool-call history.

## Risks and Tradeoffs
- This is not a configurable tool registry yet. It is a runtime-backed tool catalog and usage dashboard.
- The current workflow has one tool, `search_documents`; additional tools should be added to the catalog when they become runtime-supported.
- Timeout and retry policy are descriptive because the current tool execution path does not yet have per-tool config fields.

## Interview Notes
This ticket is useful for explaining the difference between a fake platform page and backend-supported product logic. The page does not invent tool state. It exposes the actual LangChain tool definition and aggregates persisted `ToolCall` rows so developers can inspect how tools behave in LangGraph runs.
