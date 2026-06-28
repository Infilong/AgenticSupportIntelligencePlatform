# Evaluation Agent Picker Bounded Search

## Goal
Decouple the Evaluation target-agent picker from the paginated Agent Management page so evaluation setup remains usable when the workspace has many agents.

## Context
The Agent library now loads one backend-filtered page at a time. Reusing that page as the Evaluation target-agent dropdown would make evaluation setup depend on whichever agent folder/page happened to be loaded. That is confusing and does not scale as agent names grow.

## Requirements
- Add a dedicated Evaluation target-agent search input.
- Load bounded agent options from `GET /agents?search=...&limit=...`.
- Keep the blank option for the system-v1 default evaluation agent.
- Preserve a selected agent option even when it is not in the latest search result page.
- Add a shortcut to use the currently selected operational agent.

## Non-goals
- Do not add a new backend endpoint; reuse the existing paginated agent list API.
- Do not change evaluation run execution or agent model routing.
- Do not load all agents into the browser.

## Design Plan
- Add `evaluationAgentOptions` and `evaluationAgentSearch` state.
- Load options only on the Evaluations tab and only when the user has `agents:read`.
- Update `evaluationAgentLabel()` to resolve labels from the dedicated option list as well as the Agent page list and summary fallback.
- Replace the broad agent dropdown with a bounded search plus select.

## Test Plan
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Evaluation target-agent selection no longer depends on the Agent page's current folder/page.
- The picker stays bounded as agent count grows.
- Selected agent labels remain understandable in evaluation detail views.

## Risks
- Search-specific total count is not shown; the picker intentionally loads a small option set.
- Very large workspaces may later need a reusable async entity-picker component with folders and keyboard navigation.

## Human Review Checklist
- Confirm the Evaluation form explains default agent behavior clearly.
- Confirm the search field and target dropdown are understandable.
- Confirm selecting the operational agent is useful and not visually noisy.

## Interview Notes
This ticket is a small but important product-quality fix: after introducing pagination, dependent form fields need their own bounded data access path instead of borrowing a page from another console area.
