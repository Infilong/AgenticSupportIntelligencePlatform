# Attention Evaluation Comparison Deeplink

## Goal
Make evaluation-regression tasks open the actual comparison evidence instead of only selecting the current evaluation run.

## Context
The attention queue now detects latest-vs-previous evaluation regressions, but the task only carried one target id. Clicking it opened the Evaluation page with the current run selected, while the operator still had to manually choose the baseline. For a professional operations console, task actions should route directly to the evidence needed to resolve the issue.

## Requirements
- Keep existing attention items compatible.
- Add optional task context for routes that need more than one id.
- Include baseline evaluation run id and name on evaluation-regression tasks.
- Make frontend task clicks open the selected evaluation run and automatically load the comparison.
- Keep workspace scoping enforced by the existing comparison endpoint.

## Implementation
- Added optional `target_context` to attention item service, schema, and API response.
- Added `baseline_run_id` and `baseline_run_name` context to `evaluation_regressions` tasks.
- Updated frontend `AttentionItem` type.
- Updated `loadEvaluationDetail()` to optionally fetch a baseline comparison after loading the run.
- Updated `openAttentionItem()` to pass the baseline id from task context.
- Extended attention regression tests to assert target context.

## Validation
- `cd backend && uv run pytest -s -q tests/test_attention.py` passed.
- `cd backend && uv run ruff check app/api/v1/attention.py app/schemas/attention.py app/services/attention_service.py tests/test_attention.py` passed.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run build` passed.
- `cd frontend && npm test -- --run` passed.
- `git diff --check` passed.

## Human Review Checklist
- Click an Evaluation regressions task from My Tasks or Overview.
- Confirm the Evaluations page opens with the regressed run selected.
- Confirm the Regression comparison panel is already populated against the baseline run.
- Confirm non-evaluation attention items still route as before.

## Interview Notes
This is a workflow polish detail that matters in production tools: alerts should deep-link to evidence. The backend owns the task context, and the frontend uses it without guessing or loading unbounded history.
