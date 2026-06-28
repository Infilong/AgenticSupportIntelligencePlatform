# Backend-Bounded Resource List Filters

## Goal
Make growing workspace resource libraries safer for implementation and demo use by adding backend-supported `search` and `limit` filters to list APIs for uploaded or user-managed resource collections.

## Context
The UI already organizes datasets, knowledge documents, agents, and evaluation runs into folders and caps visible rows. Before this ticket, several frontend loaders still requested unbounded lists, and the backend only exposed `folder_id` on some routes. That made large workspaces too dependent on client-side slicing.

## Requirements
- Add optional `search` and `limit` query parameters to resource list endpoints.
- Preserve workspace isolation and existing folder validation.
- Keep `limit` opt-in so existing API callers are not silently truncated.
- Bound accepted `limit` values to avoid accidental very large responses.
- Keep frontend folder counts stable for now while avoiding unbounded resource fetches.
- Add tests proving search/limit behavior across resource types.

## Non-goals
- Do not introduce a paginated response envelope yet.
- Do not replace client folder counts with backend count APIs in this ticket.
- Do not refactor the large frontend file.
- Do not change destructive resource permissions.

## Design Plan
- Backend services accept `search` and `limit` for:
  - knowledge documents
  - datasets
  - agent configs
  - evaluation runs
- API routes expose:
  - `search: string | null`, max length 120
  - `limit: int | null`, range 1-500
- Search targets stable operator-facing fields:
  - knowledge: title, language, status
  - datasets: name, description
  - agents: name, settings JSON
  - evaluations: name, modes JSON, status
- Frontend loaders request `limit=500` for major resource lists. Client folder filtering remains stable until the server-side counts/pagination ticket.

## Files Changed
- `backend/app/api/v1/knowledge.py`
- `backend/app/api/v1/datasets.py`
- `backend/app/api/v1/agents.py`
- `backend/app/api/v1/evaluations.py`
- `backend/app/services/knowledge_service.py`
- `backend/app/services/dataset_service.py`
- `backend/app/services/agent_service.py`
- `backend/app/services/evaluation_runner.py`
- `backend/tests/test_resource_folders.py`
- `frontend/src/App.tsx`

## Test Plan
- Focused backend regression: `uv run pytest -s -q tests/test_resource_folders.py`
- Backend lint: `uv run ruff check .`
- Frontend typecheck: `npm run typecheck`
- Frontend production build: `npm run build`
- Browser smoke: `make frontend-e2e-docker`

## Acceptance Criteria
- Resource list endpoints still enforce workspace permissions through existing dependencies.
- Cross-workspace folder IDs remain rejected.
- Search returns only matching resources inside the workspace/folder scope.
- Limit returns bounded result sizes.
- Existing resource lifecycle and folder tests continue to pass.
- Frontend builds and browser smoke remains green.

## Risks
- Frontend still uses client-side folder counts from fetched rows, so true server pagination/count metadata is still a future need.
- Searching JSON settings for agents is pragmatic but not a long-term indexed search strategy.
- `ILIKE` filters are acceptable for local-first scale but should become indexed search for very large workspaces.

## Human Review Checklist
- Confirm the API shape is understandable: `folder_id`, `search`, `limit`.
- Confirm `limit` being opt-in on the backend is the right compatibility choice.
- Confirm frontend `limit=500` is acceptable for the local-first v1.
- Confirm the next pagination/counts ticket is not needed before further agent-platform work.

## Interview Notes
- Explain why frontend-only slicing is not enough for scalable admin tools.
- Explain why this ticket adds bounded APIs without prematurely designing cursor pagination.
- Explain how workspace isolation is preserved by adding filters inside existing workspace-scoped queries.
