# AI Run Step Linkage

## Goal
Make AI observability structurally reliable by linking every model call to the graph run and graph step that caused it.

## Audit Finding
The trace API exposed AI run details, but the underlying `AIRun.graph_run_id` and `AIRun.graph_step_id` fields were still mostly empty. `GraphStep` also had nullable token/cost fields that were not being copied from linked AI runs. This weakened traceability and made cost attribution depend on indirect step IDs.

## Changes Made
- Added optional `graph_run_id` and `graph_step_id` arguments to `MockModelProvider.complete`.
- Passed `graph_run_id` into classification and draft model calls from the LangGraph runner.
- Added graph runtime linkage after each model-calling step is persisted:
  - set `AIRun.graph_run_id`
  - set `AIRun.graph_step_id`
  - copy `AIRun.total_tokens` to `GraphStep.token_count`
  - copy `AIRun.estimated_cost` to `GraphStep.estimated_cost`
- Strengthened backend tests to assert AI runs are linked to the graph run and graph step, and model-calling graph steps have token/cost values.

## Verification
- `make backend-lint`
- `make backend-test`
- `npm run test`
- `npm run build`
- `docker compose up -d --build api`
- Live API smoke confirmed two AI runs attach to two graph steps and step token/cost values are populated.

## Remaining Risks
- Prompt templates are still not persisted for current LangChain prompt helpers, so prompt versioning is not yet fully demonstrable in trace.
- Guardrails are still run-level records with `graph_step_id = null`; future work should attach applicable guardrails to specific graph steps.

## Next Recommended Ticket
Persist prompt templates for LangChain classification and draft prompts, record prompt template/version on `AIRun`, and render prompt/template details in the trace workbench.
