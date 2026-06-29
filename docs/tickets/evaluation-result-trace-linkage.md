# Evaluation Result Trace Linkage

## Goal
Connect system-v1 evaluation results to the exact LangGraph trace that produced each result, so failed cases can be debugged from evaluation evidence instead of remaining detached report rows.

## Context
The evaluation runner already executes system-v1 cases through the real agent service, which creates persisted graph runs, graph steps, AI run ledger entries, tool calls, guardrail results, and checkpoints. However, evaluation results only stored aggregate answer, route, scores, token, and cost fields. The trace existed but was not linked from the evaluation result.

## Requirements
- Store a nullable graph run id on evaluation results.
- Populate the graph run id only when a real system-v1 agent execution occurs.
- Keep direct LLM and vector RAG baselines unlinked because they do not create LangGraph traces.
- Expose the graph run id through the evaluation detail API.
- Show an Open trace action in the evaluation dashboard only when trace evidence exists.
- Keep workspace isolation by using the existing trace endpoint and workspace-scoped evaluation result responses.

## Non-goals
- Do not create fake trace ids for deterministic baselines.
- Do not duplicate graph step or AI run data into evaluation rows.
- Do not change metric calculation.
- Do not redesign the evaluation dashboard.

## Implementation
- Added nullable evaluation_results.graph_run_id with an index and SET NULL foreign key to graph_runs.
- Added graph_run_id to EvaluationResultResponse.
- Updated EvaluationRunner._run_case() to store the graph run id after successful system-v1 execution.
- Updated the evaluation dashboard result cards to show Open trace for linked system-v1 rows.
- Added backend test assertions that system-v1 results have trace links, baselines do not, and the linked trace endpoint is readable.

## Validation Plan
- Run focused evaluation tests.
- Run backend ruff on changed backend files and migration.
- Run frontend typecheck.
- Run frontend production build.
- Run frontend test wrapper.
- Run diff whitespace check.

## Human Review Checklist
- Confirm failed system-v1 evaluation cases now have a clear path to trace evidence.
- Confirm direct/vector baselines do not pretend to have LangGraph traces.
- Confirm cross-workspace trace access is still guarded by the existing trace endpoint.
- Confirm the dashboard remains readable when many cases are listed.

## Interview Notes
This ticket is a strong AI-platform story: evaluation is not just aggregate metrics. Each system-v1 case is linked back to the persisted LangGraph execution, which lets engineers debug retrieval evidence, guardrails, prompt versions, model calls, token cost, and routing decisions from the quality report.
