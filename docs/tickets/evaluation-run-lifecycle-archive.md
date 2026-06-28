# Evaluation Run Lifecycle Archive

## Goal
Make evaluation runs manageable as production quality evidence. Owners should be able to archive stale runs without deleting results, metrics, or audit history, and operators should be able to filter/search evaluation history as the workspace grows.

## Context
The evaluation system already supported JSONL execution, baseline comparison, stored results, and per-language metrics. The missing lifecycle control made the page feel like a growing flat log: every run remained active forever, with no owner cleanup path.

## Requirements
- Add `archived_at` to `EvaluationRun`.
- Hide archived runs from the default evaluation list.
- Support `include_archived=true` for audit/history views.
- Add owner-only archive endpoint.
- Preserve evaluation results and metrics after archive.
- Add frontend search, status filter, show-archived toggle, and archive action.
- Record archive in audit logs.
- Test owner archive, member denial, workspace isolation, and preserved detail.

## Non-goals
- No hard delete.
- No restore endpoint yet.
- No evaluation suite/folder model yet.
- No LLM-as-judge scoring.

## Backend Changes
- Added Alembic migration `0014_evaluation_run_archive`.
- Added `EvaluationRun.archived_at`.
- Added `EvaluationRunner.list_runs(include_archived=False)`.
- Added `EvaluationRunner.archive_run`.
- Added `DELETE /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}` using workspace-owner permission.
- Added `include_archived` query support to the list endpoint.

## Frontend Changes
- Evaluation run list now filters by search text and status.
- Archived runs are hidden by default and can be included with a toggle.
- Owners can archive active evaluation runs from the list.
- Run cards show archived state while preserving detail inspection.

## Validation
- `cd backend && uv run ruff check app/models/evaluation.py app/schemas/evaluation.py app/services/evaluation_runner.py app/api/v1/evaluations.py tests/test_evaluations.py alembic/versions/0014_evaluation_run_archive.py`: passed.
- `cd backend && uv run pytest -s -q tests/test_evaluations.py`: 6 passed.
- `cd backend && uv run ruff check . && uv run pytest -s -q`: full backend validation passed, 131 tests passed.
- `cd frontend && npm test`: passed.
- `cd frontend && npm run build`: passed.
- `DATABASE_URL=postgresql+psycopg://agentic:agentic@127.0.0.1:5432/agentic_support uv run alembic upgrade head`: applied `0014_evaluation_run_archive`.
- Live API smoke: archived one evaluation run, default list returned 0, `include_archived=true` returned 1 with `archived_at`.
- `docker compose up -d --build api frontend`: passed.
- `make frontend-e2e-docker`: passed.

## Human Review Checklist
- Run an evaluation from the UI.
- Confirm it appears in Evaluation runs.
- Archive it as an owner.
- Confirm it disappears from the default run list and reappears when "Show archived runs" is enabled.
- Confirm its result dashboard can still be inspected.

## Interview Notes
This is a production-minded lifecycle choice: evaluation results are quality evidence, so stale runs should be archived rather than destroyed. The design keeps active baselines focused while preserving auditability and historical comparison.
