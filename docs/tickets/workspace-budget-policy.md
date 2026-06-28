# Workspace Budget Policy and Rate Limits

## Goal
Add backend-supported workspace budget policy so token economy is enforced by runtime behavior, not only described in dashboards.

## Context
The project treats token economy as a first-class requirement. Before this ticket, the Cost page summarized AI run ledger data, but workspace-level monthly budgets and rate limits were not configurable or enforced.

## Requirements
- Persist one budget policy per workspace.
- Let workspace members read the policy.
- Let only workspace owners update the policy.
- Include current-month token and estimated-cost usage in cost summary responses.
- Show budget posture in System Health.
- Enforce hourly agent run rate limits before creating new graph runs.
- Use the lower of the agent token budget and workspace per-run token cap during graph execution.
- Record audit logs when owners update policy.
- Add tests for defaults, updates, permissions, cost summary, system health, and rate-limit denial.

## API
- `GET /api/v1/workspaces/{workspace_id}/budget-policy`
- `PUT /api/v1/workspaces/{workspace_id}/budget-policy`
- `GET /api/v1/workspaces/{workspace_id}/costs/summary` now includes `budget_policy`.

## Data Model
`WorkspaceBudgetPolicy` stores monthly token budget, monthly cost budget, per-run token budget, per-run cost budget, hourly request limit, alert threshold, timestamps, and `workspace_id`.

## Frontend
Usage & Costs now displays budget usage metrics and an owner-gated policy form. Settings links to Usage & Costs for budget/rate-limit configuration instead of mixing advanced controls into workspace identity settings.

## Verification
- `cd backend && uv run ruff check .` passed.
- Focused backend tests for budget policy, system health, and agent budget behavior passed.
- Full backend suite passed with `cd backend && uv run pytest -s -q`: 134 passed.
- Frontend typecheck passed with `cd frontend && npm test -- --run`.
- Frontend production build passed with `cd frontend && npm run build`.
- Local Postgres migration passed with `make backend-migrate`.
- Docker API/frontend rebuild passed with `docker compose up -d --build api frontend`.
- Live API smoke passed for register/login, workspace creation, budget-policy read/update, and cost summary policy reporting.
- Browser smoke passed with `make frontend-e2e-docker`.

## Human Review Checklist
- Confirm default budget values are reasonable for a local demo.
- Confirm owner/member behavior matches the intended local-team workflow.
- Confirm Usage & Costs makes the enforced policy obvious, not just advisory.
- Confirm the rate-limit error is understandable in the app when users run agents too frequently.
