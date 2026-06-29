# Evaluation Prompt-Version Evidence

## Goal
Show which prompt template versions and model-call purposes contributed to each system-v1 evaluation result, using the existing AI run ledger instead of inventing a fake prompt-quality score.

## Context
Evaluation results already compare modes, expose per-language metrics, and link system-v1 rows to graph traces. The missing product evidence was prompt lineage: when an evaluation passes or fails, a developer should see which prompt templates and versions were actually used before opening the full trace.

## Requirements
- Add backend-backed prompt/version evidence to evaluation result responses.
- Scope evidence by workspace and graph run ids.
- Do not include prompt text in the evaluation summary response.
- Baseline modes without graph runs must return empty prompt evidence.
- Show compact prompt evidence in the Evaluation dashboard result cards.
- Keep the full trace as the place for complete model-call inspection.

## Implementation
- Added `EvaluationPromptVersionResponse`.
- Evaluation detail responses now group `AIRun` rows by graph run, prompt template, prompt version, language, purpose, provider, and model.
- Each group includes AI run count, prompt tokens, completion tokens, total tokens, and estimated cost.
- System-v1 evaluation result cards now show a compact Prompt evidence section with template name, version, purpose, language, model, token count, and cost.
- The JSON details panel now includes prompt evidence for deeper inspection.

## Backend/API Impact
- `EvaluationResultResponse` gained a `prompt_versions` array.
- No database migration was needed because the data already exists in `ai_runs` and `prompt_templates`.
- The API does not expose prompt template text in evaluation summaries; prompt text remains available through trace inspection where appropriate.

## Validation Plan
- `cd backend && uv run pytest -s -q tests/test_evaluations.py`
- `cd backend && uv run ruff check app/api/v1/evaluations.py app/schemas/evaluation.py tests/test_evaluations.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `cd frontend && npm test -- --run`
- `docker compose up -d --build api frontend`
- `make frontend-e2e-docker`
- `git diff --check`

## Risks
- Evaluation response size can grow if a graph run produces many AI calls. The UI currently displays the first four groups and directs users to the trace for full detail.
- The evidence proves prompt lineage and token/cost contribution, not causal prompt quality. Quality comparison still belongs in evaluation metrics and regression comparisons.

## Human Review Checklist
- Confirm system-v1 results show prompt evidence while direct/vector baseline rows do not.
- Confirm the evidence uses real prompt template names and versions.
- Confirm no prompt source text is exposed in the evaluation result summary.
- Confirm Open trace still shows full model and prompt-call detail.

## Interview Notes
This is a defensible AI-platform feature: evaluation quality must be explainable by artifact lineage. The platform can now connect a failed or passed case to the exact prompt template versions and model purposes involved, while keeping the evaluation UI compact and the full trace available for deeper debugging.
