# Browser Smoke Evaluation Result Trace Link

## Goal
Protect the evaluation-to-trace debugging workflow in browser QA so a user can move from a system-v1 evaluation result to the exact persisted LangGraph trace.

## Context
The backend now stores evaluation_results.graph_run_id for real system-v1 evaluation cases, and the Evaluation dashboard shows Open trace when that evidence exists. That behavior is central to the professional AI platform story because evaluations must be debuggable, not just aggregate reports.

## Requirements
- Seed a real system-v1 evaluation through the API during the browser smoke test.
- Assert the API result includes a graph_run_id before the UI workflow uses it.
- Select the system-v1 evaluation in the Evaluation dashboard.
- Click Open trace from the system-v1 result card.
- Verify the Trace page opens with the same graph run id loaded and trace detail visible.

## Non-goals
- Do not add fake trace ids to baseline evaluation modes.
- Do not create a separate slow browser suite for this single workflow.
- Do not broaden the smoke test into exhaustive evaluation assertions.

## Implementation
- Extended frontend/tests/e2e/review-ux-smoke.spec.ts with a system-v1 evaluation using the seeded agent and knowledge document.
- Added browser assertions for the Evaluation result Open trace action and loaded Graph run id.

## Validation Plan
- Run frontend typecheck.
- Run frontend production build.
- Run frontend unit test wrapper.
- Rebuild API/frontend containers.
- Run make frontend-e2e-docker.
- Run diff whitespace check.

## Validation
- cd frontend && npm run typecheck: passed.
- cd backend && uv run pytest -s -q tests/test_evaluations.py: passed, 13 tests with one Starlette/httpx deprecation warning.
- cd frontend && npm run build: passed.
- cd frontend && npm test -- --run: passed.
- docker compose up -d --build api frontend: rebuilt and restarted API/frontend services.
- make frontend-e2e-docker: passed, 2 browser smoke tests.

## Human Review Checklist
- Confirm a failed or suspicious system-v1 evaluation result can be debugged without manually copying a run id.
- Confirm baseline evaluation modes still do not show trace actions unless the backend records one.
- Confirm the smoke test remains focused enough to run regularly.

## Interview Notes
This ticket demonstrates testable AI operations UX: quality reports are connected to trace evidence, and browser QA proves that developers can jump from evaluation failure to LangGraph execution details.
