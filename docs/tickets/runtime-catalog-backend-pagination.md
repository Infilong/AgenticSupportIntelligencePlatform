# Runtime Catalog Backend Pagination

## Goal
Keep the Tools and Guardrails operations pages usable as runtime-discovered tools, guardrail policies, tool calls, and guardrail failures accumulate.

## Context
Tools and guardrails are runtime catalogs, not uploaded file resources. They should not get folders in v1, but they still need backend search/view/offset controls so the frontend does not load and filter unbounded catalogs locally.

## Requirements
- Add backend search, view, `limit`, and `offset` controls for `/tools`.
- Add backend search, view, `limit`, and `offset` controls for `/guardrails`.
- Preserve workspace-scoped usage summaries and recent execution/failure context.
- Keep tool and guardrail configuration APIs unchanged.
- Wire frontend filter/search controls to backend-loaded catalog pages.
- Keep recent executions/failures attached to loaded catalog rows.

## Non-goals
- No folder semantics for runtime catalogs.
- No deletion for tools or guardrails; they are runtime definitions and governance evidence.
- No total-count endpoint in this ticket.
- No changes to LangGraph execution behavior.

## Implementation Notes
- `ToolService.list_tools()` now filters resolved effective tool definitions by search/view and applies bounded offset/limit.
- `GuardrailCatalogService.list_guardrails()` now filters resolved effective guardrail policies by search/view and applies bounded offset/limit.
- Tool search includes definitions, permissions, schemas, workflow nodes, and recent execution context.
- Guardrail search includes definition metadata, effective policy values, workflow nodes, and recent failure messages.
- The frontend Tools and Guardrails pages now reset page state on search/view changes and display backend-loaded pagination controls.

## Validation
- `cd backend && uv run ruff check app/api/v1/tools.py app/services/tool_service.py app/api/v1/guardrails.py app/services/guardrail_catalog_service.py tests/test_tools.py tests/test_guardrails.py` -> passed.
- `cd backend && uv run pytest -s -q tests/test_tools.py tests/test_guardrails.py` -> 12 passed, 1 warning.
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.
- `git diff --check` -> passed.

## Human Review Checklist
- Confirm Tools search and view filters do not feel like a flat growing catalog.
- Confirm Guardrails search and view filters still expose configurable/fixed/routing policy distinctions.
- Confirm recent executions and failures still link to traces.
- Confirm loaded-count wording is acceptable until a total-count endpoint exists.

## Interview Notes
This ticket shows a pragmatic distinction between uploaded user libraries and runtime catalogs. Runtime catalogs do not need folders, but they still need backend filtering and pagination so the operations UI scales honestly as the system discovers more tools and guardrail outcomes.
