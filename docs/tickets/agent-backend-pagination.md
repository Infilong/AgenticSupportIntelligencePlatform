# Agent Backend Pagination

## Goal
Make the Agent library scalable and folder-managed the same way Knowledge documents and Datasets are. The frontend must not depend on loading a large local agent catalog and then filtering it in the browser.

## Context
Users asked that frontend areas that can grow with more file names or resource names must be managed through folders so the page does not grow uncontrollably. Agents are not uploaded files, but they are a core platform resource that can grow by client, product, environment, experiment, or language. Existing `ResourceFolder` support already covers `agent_config` folders and backend folder counts.

## Requirements
- Add backend `folder_id`, `unfiled`, `search`, `limit`, and `offset` support for `GET /api/v1/workspaces/{workspace_id}/agents`.
- Reject conflicting `folder_id` plus `unfiled` filters.
- Keep archived agents excluded by default unless `include_archived=true` is requested.
- Keep workspace permission checks unchanged.
- Change the Agent page to fetch agents by selected folder, search, page offset, and limit.
- Show previous/next controls and backend-backed folder counts.
- Preserve selected-agent detail through the operational summary when the selected agent is not on the currently loaded page.

## Non-goals
- Do not hard-delete agents. Agent lifecycle remains archive-based so traces, evaluations, and cost attribution stay auditable.
- Do not add nested folders or bulk operations.
- Do not change LangGraph execution behavior.
- Do not paginate evaluation runs in this ticket.

## Design Plan
- Extend `AgentService.list_agents()` with `unfiled` and `offset` arguments.
- Extend the agents API route with query validation and a structured `agent_filter_conflict` error.
- Add resource-folder tests for agent folder pagination, unfiled filtering, search, and conflict rejection.
- Add `agentPage` state and `agentListParams()` in `frontend/src/App.tsx`.
- Replace local `filterByFolder()` and client-side search inside `AgentPanel()` with the backend response list.
- Reset agent page and clear search when creating a new agent so the newly created agent is visible in its target folder.

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_resource_folders.py tests/test_agents.py`
- `cd backend && uv run ruff check .`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Agent list API supports backend folder/unfiled/search/limit/offset filtering.
- Invalid `folder_id` plus `unfiled` returns 400 with `agent_filter_conflict`.
- Agent page shows a page of backend-loaded agents and page controls.
- Folder counts remain authoritative through the existing counts endpoint.
- Existing agent run, summary, archive, and move workflows keep working.

## Risks
- Search results do not have a total count endpoint yet; the UI enables Next when the current search page is full.
- Agent dropdown is scoped to the current page, so very large libraries require folder/search/page navigation before selecting an agent.
- Evaluation run history still uses the older bounded fetch pattern and should be the next pagination ticket.

## Human Review Checklist
- Confirm the Agents page clearly shows current folder, create target, search, and page controls.
- Confirm moving an agent between folders updates the visible folder scope and counts.
- Confirm archive remains permission-aware and does not imply hard delete.
- Confirm the UI does not stretch when many agents exist.

## Interview Notes
This ticket demonstrates a professional resource-library pattern: folder organization, backend filtering, pagination, permission-aware lifecycle actions, and truthful backend counts. It is a small platform-scale improvement that avoids pretending a local browser filter is enough for a growing AI operations console.
