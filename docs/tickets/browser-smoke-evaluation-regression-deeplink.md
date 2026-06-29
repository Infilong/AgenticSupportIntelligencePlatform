# Browser Smoke Evaluation Regression Deeplink

## Goal
Protect the evaluation-regression task workflow with browser-level coverage so the professional operations path stays intuitive after UI changes.

## Context
The backend attention queue now detects evaluation regressions and includes baseline context. The frontend opens the selected evaluation run and comparison panel from My Tasks. This is exactly the kind of professional UX behavior that build/typecheck cannot prove, so the Docker Playwright smoke path should cover it.

## Requirements
- Create baseline and regressed evaluation runs through the real API in the smoke setup.
- Open My Tasks from the browser UI.
- Confirm the Evaluation regressions task appears with baseline context.
- Click Compare evaluation and confirm the Evaluation dashboard opens with the regression comparison panel populated.
- Keep the existing focus-stability and permission-smoke coverage intact.

## Implementation
- Updated `frontend/tests/e2e/review-ux-smoke.spec.ts` to create a passing baseline evaluation and a regressed latest evaluation.
- Added browser assertions for My Tasks -> Evaluation regressions -> Compare evaluation -> Regression comparison.
- Updated stale smoke locators for current Evaluation and Trace page labels.

## Validation
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run` passed.
- `docker compose up -d --build api frontend` rebuilt the app containers.
- First `make frontend-e2e-docker` run found a stale `Selected run` locator and it was fixed with `exact: true`.
- Second `make frontend-e2e-docker` run found a stale Trace heading assertion and it was updated from `Trace entry points` to `Run history`.
- Final `make frontend-e2e-docker` passed: 2 passed.
- `git diff --check` passed.

## Human Review Checklist
- Confirm the My Tasks regression card is understandable to an operator.
- Confirm the comparison evidence appears without manually selecting a baseline.
- Confirm the smoke still covers reviewer permissions and input focus stability.

## Interview Notes
This shows that high-value AI operations workflows are verified in a real browser against the API, not just by unit tests. It catches stale labels and protects the path from alert to evidence.
