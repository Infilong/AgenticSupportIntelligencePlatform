# Evaluation Operations Board

## Goal
Make Evaluation history feel like a professional AI platform operations surface instead of a growing run list next to a JSONL editor. Users should be able to filter run history, understand selected-run coverage, and drill into language/mode quality evidence without losing the backend truth.

## Context
Evaluations are central to the portfolio story: they prove multilingual behavior, baseline comparison, routing quality, and token economy. The backend already stores evaluation runs, results, metrics, modes, archive timestamps, and workspace scope. The frontend already showed a dashboard for a selected run, but run history needed stronger operational filtering and bounded display behavior.

## Requirements
- Use existing evaluation API data only.
- Add run-history views for active, all, failed, selected, and archived runs.
- Keep existing status filter, search, archive toggle, inspect action, and owner-gated archive control.
- Search by run name, mode, status, or id.
- Show selected-run coverage from persisted result rows: languages, modes, result count, and failure count.
- Bound visible run rows so evaluation history does not become an unbounded panel.
- Add browser coverage using a real evaluation run created through the backend API.

## Non-goals
- No new evaluation metrics.
- No backend schema changes.
- No fake LLM-as-judge or quality scoring.
- No pagination until backend list sizes require it.

## Implementation Notes
- Added `EvaluationRunView` and filter options.
- Added `MAX_VISIBLE_EVALUATION_RUNS`.
- Added `parseEvaluationModes` and `evaluationRunMatchesView` helpers.
- Reworked the run selector into an `Evaluation operations board` with selected-run coverage and segmented run filters.
- Capped displayed matching runs and added guidance when matches exceed the cap.
- Extended Playwright smoke setup to create a real evaluation run via `/evaluations`, then search and select it in the UI.

## Verification
- `cd frontend && npm test -- --run` passed.
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt and restarted the composed frontend/API stack.
- `make frontend-e2e-docker` passed, including creation of a real backend evaluation run, Evaluation board search/selection, Data and Knowledge folder search focus, Tools search focus, Guardrail search focus, trace navigation, and human-review editor focus.

## Human Review Checklist
- Confirm the Evaluation page makes baseline comparison and selected-run coverage obvious.
- Confirm archived runs are still accessible but not mixed into active history unless requested.
- Confirm search and filters do not hide the selected dashboard unexpectedly.
- Confirm this remains honest about current deterministic metrics and does not imply unsupported quality judgment.
