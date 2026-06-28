# Workspace Tool Defaults

## Goal
Make agent tools first-class configurable workspace resources instead of static catalog rows.

## Context
The Tools page already displayed name, schema, timeout, retry policy, enabled status, usage, and history, but those fields came from static definitions. The active goal requires tool defaults, backend-supported product logic, tool execution traceability, and permission-aware controls.

## Requirements
- Persist workspace-scoped tool config.
- Allow owners to update `enabled`, `timeout_ms`, and `max_retries`.
- Keep tool catalog workspace-scoped.
- Show tool config in the frontend with draft-and-save controls.
- Disable owner-only controls for users without `tools:configure`.
- Make LangGraph runtime respect disabled `search_documents`.
- Persist a failed `ToolCall` and failed graph step when a disabled tool would have been used.
- Add an Alembic migration for the new table.

## Non-goals
- No distributed tool execution service.
- No actual timeout enforcement wrapper yet.
- No automatic retry loop yet.
- No arbitrary custom tool authoring UI.

## Design Plan
- Add `ToolConfig` model and migration.
- Add tool config schema fields and PATCH endpoint.
- Merge `ToolConfig` into runtime tool definitions in `ToolService`.
- Update graph runtime to route disabled retrieval tool attempts into traceable failure/review state.
- Add frontend tool default controls with explicit Save action.

## Test Plan
- Focused tool catalog and runtime tests.
- Frontend typecheck/build.
- Full backend lint/test suite.
- Alembic upgrade against live Docker Postgres.
- Docker rebuild and live smoke of tool config endpoint.

## Acceptance Criteria
- Owners can configure tool defaults.
- Members cannot mutate tool defaults.
- Tool config is workspace-scoped.
- Disabled retrieval tool prevents retrieval, records a failed tool call, and routes to human review.
- Tool UI shows editable defaults and execution history together.

## Risks
- Timeout and retry values are persisted and visible but not fully enforced except disabled/enabled behavior. This is documented honestly until a worker/runtime retry wrapper is added.
- The local Docker API does not auto-run Alembic, so validation must include `alembic upgrade head` against the live database.

## Human Review Checklist
- Confirm Tools page makes defaults, schemas, and history understandable.
- Confirm typing in timeout/retry fields does not trigger focus loss.
- Confirm non-owner users see read-only controls.
- Confirm disabled `search_documents` creates a traceable failed retrieve step.

## Interview Notes
This ticket upgrades tools from hidden implementation details to governed platform resources. It also demonstrates the difference between UI-only polish and product integrity: the backend stores configuration, enforces authorization, records audit events, and the LangGraph runtime changes behavior based on the config.

## Validation Results
- `cd backend && uv run ruff check app tests/test_tools.py tests/conftest.py`: passed after formatting/import fix.
- `cd backend && uv run pytest tests/test_tools.py -q -s`: 5 passed, 1 Starlette/httpx deprecation warning.
- `cd frontend && npm run test -- --run`: passed TypeScript check.
- `cd frontend && npm run build`: passed.
- `cd backend && uv run ruff check .`: passed.
- `cd backend && uv run pytest -q -s`: 126 passed, 1 Starlette/httpx deprecation warning.
- `git diff --check`: passed.
- `cd backend && DATABASE_URL=postgresql+psycopg://agentic:agentic@localhost:5432/agentic_support uv run alembic upgrade head`: applied `0012_tool_configs` to live Docker PostgreSQL.
- `docker compose up -d --build api frontend`: rebuilt and restarted services.
- Live smoke `PATCH /api/v1/workspaces/{workspace_id}/tools/search_documents/config`: persisted `enabled=false`, `timeout_ms=3500`, `max_retries=1` and catalog returned the same values.
- Live smoke `GET http://127.0.0.1:5173`: returned frontend HTML.
