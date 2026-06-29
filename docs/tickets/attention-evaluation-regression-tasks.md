# Attention Evaluation Regression Tasks

## Goal
Make My Tasks and Overview honestly surface evaluation regressions as backend-ranked operational work, not just failed evaluation cases or UI copy.

## Context
The active product objective requires users to quickly understand what needs attention. The app already had a backend attention queue and a run comparison API, but the attention service only reported failed evaluation results. The frontend copy promised evaluation regressions, so the backend needed a real regression signal.

## Requirements
- Compare the latest completed evaluation run with the previous completed run in the same workspace.
- Create an attention item when the latest run regresses on quality, token, cost, or latency metrics.
- Treat average prompt tokens, estimated cost per run, and average latency as lower-is-better.
- Treat pass-rate style metrics as higher-is-better.
- Preserve workspace scoping and avoid persisted duplicate task rows.
- Make the task open the relevant evaluation run detail from the frontend.

## Implementation
- Added computed `evaluation_regressions` attention items in `AttentionService`.
- Added metric-regression helpers with lower-is-better handling.
- Added `target_id` for evaluation failure and regression attention items.
- Updated frontend `openAttentionItem()` so evaluation tasks open the selected evaluation run detail.
- Added regression coverage using explicit completed evaluation runs and metrics.
- Updated a stale attention test to read the current human-review list envelope.

## Validation
- `cd backend && uv run pytest -s -q tests/test_attention.py` passed.
- `cd backend && uv run ruff check app/services/attention_service.py tests/test_attention.py` passed.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run` passed.
- `git diff --check` passed.

## Human Review Checklist
- Create two completed evaluation runs with metric regressions and confirm My Tasks shows Evaluation regressions.
- Click the task and confirm it opens Evaluations with the regressed run selected.
- Confirm cost/token/latency regressions are treated as lower-is-better.
- Confirm no task appears when the latest run improves or matches the previous run.

## Interview Notes
This is backend-supported product logic for AI operations. A professional platform should not make users manually inspect every evaluation report; it should promote regressions into an operational queue with a direct path to the evidence.
