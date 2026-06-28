# Workspace Attention API and My Tasks Page

## Goal
Make operational tasks first-class instead of burying them inside dashboard cards. The platform should tell each user what needs attention, why it matters, and which tool/page to open next.

## Context
The active product objective explicitly requires a task/attention workflow: pending reviews, failed agent runs, high-cost runs, guardrail blocks, evaluation regressions, tool errors, data import status, and system health. Before this ticket, the dashboard had a useful frontend-built attention section, but there was no backend-supported task queue or dedicated My Tasks page.

## Requirements
- Add a workspace-scoped backend attention summary endpoint.
- Build task items from real persisted platform signals, not static placeholders.
- Include severity, count, detail, recommended action, target tab, and timestamp where available.
- Preserve workspace isolation through the existing membership dependency.
- Add a dedicated Platform > My Tasks navigation item.
- Add a professional task queue UI with clear next action and role-oriented guidance.
- Add tests for review/guardrail signals, assigned review signals, and workspace scoping.

## Backend Changes
- Added `AttentionService` aggregating:
  - pending human reviews
  - reviews assigned to current user
  - unassigned reviews
  - failed graph runs
  - failed model calls
  - failed tool calls
  - guardrail failures
  - failed knowledge indexing
  - evaluation failures
- Added `GET /api/v1/workspaces/{workspace_id}/attention`.
- Added response schemas for attention summary and task items.
- Registered the attention router under `/api/v1`.

## Frontend Changes
- Added `Platform > My Tasks` navigation.
- Added typed `AttentionSummary` and `AttentionItem` payloads.
- Added workspace refresh loading for attention summary.
- Added `TasksPanel` with:
  - next task card
  - critical/warning/pending/assigned metrics
  - backend-generated task cards
  - action buttons routing to Reviews, Trace, Guardrails, Tools, Knowledge, Evaluations, or Costs
  - operator guidance for reviewers, developers, admins, and knowledge owners

## Verification
- `cd backend && uv run ruff check app tests/test_attention.py`
- `cd backend && uv run pytest tests/test_attention.py -q -s`
- `cd frontend && npm run test -- --run`
- `cd frontend && npm run build`

## Human Review Checklist
- Open `My Tasks` after logging in.
- Run an unsupported/no-source agent request and confirm pending review and guardrail tasks appear.
- Claim a review and confirm assigned-to-me count updates after refresh.
- Click task actions and confirm the relevant page opens.
- Confirm non-member users cannot read another workspace's attention API.

## Known Limitations
- This is an aggregated attention queue, not a durable task assignment database.
- High-cost run anomaly detection is not implemented yet; cost anomalies can be added once budgets and thresholds become configurable.
- Target IDs are currently broad except for future trace-specific task links; most actions open the relevant product area.
