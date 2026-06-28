# Trace Entry Points

## Goal
Make the Runs & traces page usable without requiring users to paste raw graph run IDs. Developers and reviewers should be able to open recent traces directly from workspace context.

## Context
The trace workbench already exposes LangGraph nodes, AI runs, tool calls, guardrails, checkpoints, token/cost data, and raw JSON drilldowns. The weak point was discoverability: the Trace page started with a graph-run-id input, so a new user had to know where to copy IDs from before seeing the strongest proof surface in the app.

## Requirements
- Keep manual graph run ID loading for audit/cost/tool cross-links.
- Add trace entry points from real frontend state: latest run, selected agent recent runs, and pending human-review runs.
- Deduplicate repeated run IDs and keep the list bounded.
- Show loaded trace summary metrics before the detailed workbench.
- Do not introduce fake/demo-only trace data.
- Add browser coverage proving a review-routed run can be opened from the Runs & traces page.

## Non-goals
- Do not add a new backend trace list endpoint in this ticket.
- Do not redesign the full TraceViewer internals.
- Do not remove raw JSON drilldowns or manual ID loading.

## Implementation Notes
- Added `buildTraceEntries` to derive trace entry points from `latestRun`, selected agent summary `recent_runs`, and pending human reviews.
- Converted trace entry, route, status, and primary signal values into readable labels while keeping raw JSON in details.
- Reworked `TracePanel` into a professional entry surface with a hero, summary metrics, trace entry list, and secondary manual loader.
- Added responsive CSS for the new trace entry layout.
- Extended the Playwright smoke path to open Runs & traces, select the review-routed run, and assert the execution navigator and runtime sections load.

## Verification
- `cd frontend && npm test -- --run` - typecheck passed
- `cd frontend && npm run build` - production build passed
- `docker compose up -d --build frontend` - rebuilt local browser target
- `make frontend-e2e-docker` - 1 passed
