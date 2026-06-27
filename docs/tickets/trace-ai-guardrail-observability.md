# Trace AI And Guardrail Observability

## Goal
Make the trace workbench a real AI engineering observability surface by exposing AI run ledger data and guardrail results through the trace API and frontend.

## Audit Finding
The backend stored `AIRun` and `GuardrailResult` records, but `/agent-runs/{run_id}/trace` only returned graph steps and tool calls. The frontend could show step IDs and raw JSON, but not the model/provider/token/cost details or persisted guardrail outcomes that engineers and admins need to debug AI workflows.

## Changes Made
- Added `AIRunTraceResponse` and `GuardrailTraceResponse` schemas.
- Extended `GraphStepResponse` with an optional inline `ai_run` object.
- Extended `GraphTraceResponse` with top-level `ai_runs` and `guardrails` arrays.
- Updated the trace route to query workspace-scoped AI runs and guardrail results for the graph run.
- Added backend regression assertions that trace responses include AI run purpose/model/token/cost and guardrail severity data.
- Updated frontend trace types and rendering to show AI run provider/model, purpose, prompt/completion/total tokens, estimated cost, cache hit state, prompt template version, and guardrail results.

## Verification
- `make backend-lint`
- `make backend-test`
- `npm run test`
- `npm run build`
- `docker compose up -d --build api frontend`
- Live API smoke: created a workspace, uploaded knowledge, ran an agent, and confirmed trace response includes `ai_runs`, `guardrails`, and inline step `ai_run` data.

## Remaining Risks
- AI runs are attached to steps through `GraphStep.ai_run_id`; `AIRun.graph_run_id` and `AIRun.graph_step_id` are still nullable and not populated by the mock provider.
- Guardrail results are currently run-level records with `graph_step_id = null`; future work should attach applicable guardrails to specific graph steps where possible.
- Prompt templates are not yet persisted for the current mock prompts, so prompt template version often shows as not versioned.

## Next Recommended Ticket
Populate `AIRun.graph_run_id` and `AIRun.graph_step_id` during graph execution, persist prompt template/version records for LangChain prompts, and add a trace detail drawer for prompt template and model configuration.
