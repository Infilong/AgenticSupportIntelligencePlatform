# Agent List Total Count Envelope

## Goal
Make the Agent library truthful under backend pagination by returning page metadata instead of a bare array. Agent configs are a first-class platform resource, so folder/search pagination should be controlled by the backend rather than guessed from the loaded page.

## Context
The Agent page already had folder organization, search, bounded rendering, archive behavior, operational summaries, workflow posture, and model route controls. `GET /agents` still returned `AgentResponse[]`, so the frontend inferred Next-page availability from page length or folder-count summaries. That breaks the professional resource-management pattern already used by datasets, knowledge documents, reviews, tools, guardrails, prompts, models, audit logs, and cost drilldowns.

## Requirements
- Change `GET /api/v1/workspaces/{workspace_id}/agents` to return `items`, `total`, `limit`, `offset`, and `has_next`.
- Preserve `include_archived`, `folder_id`, `unfiled`, `search`, `limit`, and `offset` behavior.
- Preserve folder/unfiled conflict validation.
- Keep workspace isolation and permission requirements unchanged.
- Update Agent page totals and Next button behavior to use backend metadata.
- Update Evaluation target-agent search because it reuses `GET /agents`.
- Update focused tests for archive visibility, folder/search filtering, unfiled filtering, pagination, and stale resource-folder assertions.

## Non-goals
- Do not redesign the Agent page in this ticket.
- Do not add cursor pagination in v1.
- Do not change agent execution, archive semantics, model routing, or folder APIs.

## Implementation Summary
- Added `AgentListResponse`.
- Extracted shared Agent service filter logic into `_agent_filters()`.
- Added `AgentService.count_agents()` using the same filters as `list_agents()`.
- Updated the Agents API route to return a list envelope.
- Updated React Agent state with `agentTotal` and `agentHasNext`.
- Updated `loadAgents()` and `loadEvaluationAgentOptions()` to consume `items`.
- Updated Agent library badges, folder banner, empty state, and pagination text to use backend totals.
- Updated tests in `test_agents.py` and `test_resource_folders.py` for the new contract and for existing dataset/knowledge/audit list envelopes.

## Validation
- Backend: `uv run pytest -s -q tests/test_agents.py tests/test_resource_folders.py`
- Backend lint: `uv run ruff check app tests/test_agents.py tests/test_resource_folders.py`
- Frontend: `npm run typecheck`
- Frontend: `npm run build`

## Risks
- This changes the `GET /agents` API contract; in-repo callers are updated, but external clients must read `items`.
- Agent folder sidebar counts still come from folder-count metadata, while list totals come from the active folder/search query. That split is intentional and matches the dataset/knowledge behavior.
- The active-agent selector is still a native select over the current bounded page. It remains acceptable because it mirrors the selected Agent library page, but a future UX pass can remove the duplicate selector and rely fully on library-row selection.

## Human Review Checklist
- Confirm the Agent library shows `shown of total` values that match search and folder scope.
- Confirm Next is controlled by backend `has_next`.
- Confirm Evaluation target-agent search still works after the API response shape change.
- Confirm archived agents remain hidden by default and visible with `include_archived` where used.

## Interview Notes
This ticket demonstrates API maturity for a core platform resource. Agent configs are not demo-only objects; they need stable, paginated, workspace-scoped list contracts so the UI can scale from a few agents to a large internal agent catalog without misleading the operator.
