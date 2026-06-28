# Workspace System Health Admin

## Goal
Add a truthful workspace-scoped system health surface for provider readiness, token budget posture, operational failures, data readiness, and governance/audit posture.

## Context
The app already has model configs, cost ledger, attention tasks, audit logs, guardrail results, human reviews, datasets, documents, and workspace permissions. Admin users need one place that summarizes whether the workspace is ready to operate and which page fixes each risk.

## Requirements
- Expose `GET /api/v1/workspaces/{workspace_id}/system-health` behind workspace membership.
- Report live backend state, not fake settings.
- Mark unimplemented global controls as `not_configured` instead of pretending they exist.
- Warn when live model provider routes exist without an API key.
- Surface failed graph runs, failed AI runs, pending reviews, failed documents, failed tools, and failed evaluations.
- Add an Admin navigation tab with sections and follow-up paths to Models, Tasks, Costs, and Audit.

## Non-goals
- No global budget mutation API.
- No global rate limit implementation.
- No Redis ping client dependency yet.
- No cloud infrastructure health checks.

## Design Plan
- Add system health schemas with checks, sections, and metrics.
- Add a read-only service that aggregates workspace counts from existing tables.
- Add a workspace-scoped FastAPI route.
- Add backend tests for provider warnings, workspace isolation, and operational failure counts.
- Add frontend types, loader, Admin nav tab, and a health console UI.

## Test Plan
- Run backend ruff and system health tests.
- Run frontend typecheck and production build.
- Run full backend test suite.
- Run `git diff --check`.
- Rebuild Docker frontend/API and smoke check API/frontend URLs.

## Acceptance Criteria
- Workspace members can view health; non-members cannot.
- Live provider without `OPENAI_API_KEY` reports warning.
- Operational failures are visible and counted.
- Planned controls are clearly labeled as not configured.
- Admin UI links health signals to real fix pages.

## Risks
- Redis is reported as configured-but-not-live-checked until a Redis client/ping is added.
- Global budget/rate-limit metrics are intentionally honest placeholders until backend enforcement exists.
- Browser visual QA is still blocked by missing WSL Playwright Chromium dependency `libnspr4.so`.

## Human Review Checklist
- Confirm the System health tab does not pretend to enforce controls that do not exist.
- Confirm provider/key warnings are understandable.
- Confirm the page guides users to Models, Tasks, Costs, and Audit.
- Confirm members can view but only owners can change underlying admin resources where applicable.

## Interview Notes
This ticket demonstrates operational maturity: the project does not only run LLM workflows, it exposes readiness, failure, budget, provider, and governance signals through workspace-scoped APIs. The important tradeoff is honesty: local v1 reports planned controls as not configured rather than building fake settings.

## Validation Results
- `cd backend && uv run ruff check app tests/test_system_health.py`: passed after formatting.
- `cd backend && uv run pytest tests/test_system_health.py -q -s`: 3 passed.
- `cd frontend && npm run test -- --run`: passed TypeScript check.
- `cd frontend && npm run build`: passed.
- `cd backend && uv run ruff check .`: passed.
- `cd backend && uv run pytest -q -s`: 120 passed, 1 Starlette/httpx deprecation warning.
- `git diff --check`: passed.
- `docker compose up -d --build api frontend`: rebuilt and restarted services.
- Live smoke `GET /api/v1/workspaces/{workspace_id}/system-health`: returned `overall_status=warning`, checks `api,database,redis`, and sections `providers,budgets,operations,data,governance`.
