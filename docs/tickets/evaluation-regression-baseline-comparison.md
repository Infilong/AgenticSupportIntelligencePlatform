# Evaluation Regression Baseline Comparison

## Goal
Make evaluation results useful for release and prompt/model regression work by comparing a selected run against a prior baseline run.

## Context
The Evaluation page already stored per-language metrics and presented a selected run, but the app did not have a backend-supported comparison contract. The product copy mentioned baseline comparison, yet users could only inspect one run at a time. A serious AI platform needs to show whether a candidate workflow improved or regressed against prior quality, cost, latency, and token baselines.

## Requirements
- Add a workspace-scoped comparison API between two evaluation runs.
- Compare metrics by mode, language, and metric name.
- Treat pass-rate style metrics as higher-is-better.
- Treat average prompt tokens, estimated cost per run, and average latency as lower-is-better.
- Report improved, regressed, unchanged, new, and missing metrics.
- Keep the frontend baseline picker bounded and searchable instead of using a long native dropdown.
- Do not add a migration or duplicate persisted comparison rows.

## Implementation
- Added `EvaluationMetricDeltaResponse` and `EvaluationComparisonResponse` schemas.
- Added `EvaluationRunner.compare_runs()` to compute metric deltas from existing `EvaluationMetric` rows.
- Added `GET /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}/compare/{baseline_id}`.
- Added backend coverage for delta direction, lower-is-better metrics, new/missing metrics, and cross-workspace 404 behavior.
- Added a bounded searchable baseline picker on the Evaluation dashboard.
- Added a regression comparison panel showing improvement/regression/new/missing counts and the first metric deltas.

## Validation
- `cd backend && uv run pytest -s -q tests/test_evaluations.py` passed.
- `cd backend && uv run ruff check app tests/test_evaluations.py` passed after import ordering fix.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run` passed.
- `git diff --check` passed.

## Human Review Checklist
- Confirm the Evaluation dashboard makes current-vs-baseline comparison obvious.
- Confirm cost/token/latency regressions are marked correctly as lower-is-better.
- Confirm the baseline picker stays bounded and searchable with many runs.
- Confirm comparing runs from another workspace returns not found rather than leaking existence.

## Interview Notes
This ticket turns evaluation from a static report into an operational regression workflow. That matters to AI employers because production teams need to prove that a prompt, model, retrieval, or guardrail change improved quality without increasing latency, token pressure, or cost.
