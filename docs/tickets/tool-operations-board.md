# Tool Operations Board

## Goal
Make the Tools page scale like a professional AI platform tool registry and operations surface. Developers should be able to filter runtime tools, search by contract/permission/workflow node, and inspect configuration and trace-linked executions without reading a flat card wall.

## Context
The backend already exposes a workspace-scoped tool catalog from real runtime definitions, persisted `ToolConfig`, and `ToolCall` usage history. The previous frontend showed editable tool defaults and executions, but had no board-level search/filter and used raw runtime identifiers as the primary display text.

## Requirements
- Keep the page backed by the existing `/tools` catalog and `PATCH /tools/{tool}/config` endpoint.
- Add filter modes for all tools, enabled tools, disabled tools, failed tools, and configured tools.
- Add search over friendly name, runtime name, description, framework, retry policy, permissions, and workflow nodes.
- Use friendly visible labels for known tools and framework strings while preserving exact runtime names as secondary metadata.
- Add browser coverage for the filter/search focus path and friendly tool label.

## Non-goals
- No backend schema change.
- No new tools.
- No arbitrary custom tool authoring UI.
- No claim that timeout/retry values are fully enforced beyond the current runtime behavior documented in `workspace-tool-defaults.md`.

## Implementation Notes
- Added `ToolView` state and view options.
- Added a `Tool operations board` toolbar with segmented filters, search, and workspace override count.
- Added `friendlyToolName`, `friendlyToolFramework`, `toolHasWorkspaceConfig`, and `toolMatchesView` helpers.
- Changed the primary card heading from raw `search_documents` to `Search documents`, while keeping the exact runtime identifier visible below it.

## Verification
- `cd frontend && npm test -- --run` passed.
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt and restarted the composed frontend/API stack.
- `make frontend-e2e-docker` passed with the focused Playwright smoke path for folder search, human-review editor focus, Tools search focus, friendly tool labels, and guardrail search focus.

## Human Review Checklist
- Confirm the Tools page remains honest about the single implemented v1 tool.
- Confirm owner-gated Save controls still use the existing endpoint.
- Confirm the exact runtime tool name remains available for debugging.
- Confirm the board will not become unusable when more runtime tools are added.
