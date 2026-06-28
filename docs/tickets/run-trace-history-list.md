# Run Trace History List

## Goal
Make Runs / Traces usable as a growing operations surface. A workspace can accumulate many LangGraph executions, so the Trace page must not depend on a selected agent summary or a short in-memory recent list.

## Context
The professional-platform roadmap requires traceability, human review, guardrails, token/cost observability, and clear operations history. The user also clarified that frontend fields or areas that grow with many names/files must be managed with folder or bounded navigation patterns. Graph runs are execution records rather than uploaded files, so they should use an operations history pattern: search, status filtering, backend totals, and pagination.

## Requirements
- Add a workspace-scoped `GET /agent-runs` endpoint.
- Return `items`, `total`, `limit`, `offset`, and `has_next`.
- Support status filtering for `running`, `completed`, `needs_human_review`, and `failed`.
- Support search across run message, run id, trace id, route decision, language, and agent id.
- Keep trace detail endpoints workspace-scoped.
- Update the Trace page to load run history from the backend, not only from selected-agent summaries.
- Keep pending review cases discoverable as trace entry points.

## Non-goals
- Do not add folders for graph runs in this ticket. Runs are operational records, not user-managed files.
- Do not change graph execution behavior, LangGraph node behavior, or AI model behavior.
- Do not add destructive run deletion.

## Design Summary
- Added `GraphRunListResponse` to the agent schemas.
- Added `AgentService.list_graph_runs()`, `count_graph_runs()`, and shared filters.
- Added `GET /api/v1/workspaces/{workspace_id}/agent-runs` behind `traces:read`.
- Added frontend trace history state, query builder, loader, status/search controls, and pagination.
- The Trace panel now uses backend run history plus review shortcuts instead of selected-agent summary history only.

## Test Plan
- Backend test creates completed, human-review, and failed runs directly in the database.
- Test verifies pagination metadata, newest-first ordering, status filtering, search filtering, and workspace isolation.
- Frontend validation: TypeScript and production build.

## Acceptance Criteria
- Trace history is workspace-scoped and permission-gated.
- Trace history stays bounded through backend `limit`/`offset`.
- Search and status filters do not require loading all runs into the browser.
- Other workspaces cannot see run records.
- The Trace page explains that large workspaces should use search/status filters instead of one growing list.

## Human Review Checklist
- Confirm the Trace page feels like an operations console, not a random recent-run list.
- Confirm search and status filters are understandable.
- Confirm selecting a run still opens the full trace viewer.
- Confirm run history should remain non-destructive for now.

## Interview Notes
- Explain why graph runs are treated as immutable audit/operations records rather than folder-managed files.
- Explain why the backend returns total counts and `has_next` instead of the frontend guessing from loaded rows.
- Explain how `traces:read` and workspace filters prevent cross-workspace trace leakage.
