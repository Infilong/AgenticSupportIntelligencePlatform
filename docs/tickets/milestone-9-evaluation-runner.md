# Milestone 9: Evaluation Runner

## Goal
Add an evaluation system that loads JSONL cases, runs baseline modes and `system_v1`, stores per-case results, and computes per-language metrics.

This milestone should make the project interview-defensible as an AI product: quality, routing, citations, language preservation, latency, and estimated cost become measurable rather than anecdotal.

## Context
Implemented foundation:
- multilingual knowledge ingestion.
- retrieval with citations and no-source behavior.
- AI run ledger and cost summary.
- LangGraph support-agent workflow.
- guardrails and human review routing.

Relevant docs:
- `docs/evaluation-design.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/milestone-plan.md`

## Requirements
- Add SQLAlchemy models and migration for:
  - `EvaluationCase`
  - `EvaluationRun`
  - `EvaluationResult`
  - `EvaluationMetric`
- Add JSONL loader for evaluation cases.
- Add evaluation runner that supports baseline modes:
  - `direct_llm`
  - `vector_rag`
  - `system_v1`
- Store metrics by language and mode.
- Add API routes:
  - `POST /api/v1/workspaces/{workspace_id}/evaluations`
  - `GET /api/v1/workspaces/{workspace_id}/evaluations`
  - `GET /api/v1/workspaces/{workspace_id}/evaluations/{evaluation_id}`
- Enforce workspace isolation for all evaluation data.
- Add demo JSONL cases under backend demo data.
- Add tests for schema loading, metric calculation, baseline comparison, per-language metrics, and permissions.

## Non-goals
- No real LLM evaluator.
- No frontend evaluation dashboard yet.
- No large 30-case suite in this milestone unless cheap; include a small representative demo file and design for expansion.
- No BigQuery or analytics warehouse.

## Design Plan
- Add `backend/app/models/evaluation.py`.
- Add `backend/app/schemas/evaluation.py`.
- Add `backend/app/services/evaluation_loader.py`.
- Add `backend/app/services/evaluation_metrics.py`.
- Add `backend/app/services/evaluation_runner.py`.
- Add `backend/app/api/v1/evaluations.py`.
- Add migration `0008_evaluation.py`.
- Add demo cases file `backend/demo_data/evaluations/support_eval_cases.jsonl`.
- Add tests `backend/tests/test_evaluations.py`.

## Database Migrations
```text
EvaluationCase
- id
- workspace_id
- external_id
- language
- input_message
- expected_intent nullable
- expected_sources_json
- must_include_json
- must_not_include_json
- expected_route
- safety_risk
- max_prompt_tokens nullable
- metadata_json
- created_at

EvaluationRun
- id
- workspace_id
- name
- modes_json
- status
- total_cases
- created_by_user_id
- created_at
- completed_at nullable

EvaluationResult
- id
- workspace_id
- evaluation_run_id
- evaluation_case_id
- mode
- language
- actual_route
- answer nullable
- citations_json
- passed
- scores_json
- latency_ms
- prompt_tokens
- estimated_cost
- error_message nullable
- created_at

EvaluationMetric
- id
- workspace_id
- evaluation_run_id
- mode
- language
- metric_name
- metric_value
- created_at
```

## API Design
Request:
```json
{
  "name": "Smoke evaluation",
  "jsonl_cases": "{...}\n{...}",
  "modes": ["direct_llm", "vector_rag", "system_v1"],
  "agent_id": "optional existing agent id"
}
```

Response returns run metadata, results, and metrics.

## Metrics
At minimum compute:
- `case_pass_rate`
- `human_review_routing_accuracy`
- `language_preservation_pass_rate`
- `citation_accuracy`
- `groundedness_pass_rate`
- `average_latency_ms`
- `average_prompt_tokens`
- `estimated_cost_per_run`

## Acceptance Criteria
- evaluation can run from API.
- metrics are stored.
- English/Japanese/Chinese results are separated.
- baseline comparison works.
- tests cover evaluation schema and metrics.
- workspace isolation is tested.
- validation passes and commit is pushed.

## Risks
- Fake evaluation risk: avoid pretending deterministic checks are equivalent to human quality judgment.
- Scope risk: system workflow can be expensive if every case runs every mode; use mock providers and small tests.
- Workspace risk: evaluation cases/results must be workspace-scoped.
- Metric risk: document limitations of simple string/citation checks.

## Human Review Checklist
- Verify result records are useful for debugging.
- Verify metrics are separated by language and mode.
- Verify baseline modes are honest and deterministic.
- Verify tests do not call real AI providers.

## Interview Notes
Be able to explain:
- why AI product quality must be measured by language.
- why baseline comparison matters.
- how routing accuracy, citations, groundedness, cost, and latency are calculated.
- why deterministic evals are useful but limited.

## Implementation Record
Implemented after approval.

Changed areas:
- Added evaluation models, schemas, migration, API router, JSONL loader, metric calculator, and runner service.
- Added representative English, Japanese, and Chinese demo evaluation cases.
- Added tests for loading, metrics, API execution, baseline comparison, and workspace isolation.
- Updated design docs and architecture tree to reflect the implemented evaluation system.

Validation performed:
- `make backend-lint` passed.
- `make backend-test` passed with 53 tests.
- Docker PostgreSQL/Redis migration applied through `make backend-migrate`.
- Docker API smoke created a workspace, uploaded EN/JA/ZH documents, ran 3 cases across 3 modes, and verified stored results and metrics.

Known limitations:
- Deterministic metrics are useful regression checks, not a substitute for human review or LLM-as-judge evaluation.
- Demo cases are representative; the full 30+ case suite remains portfolio-packaging work.
- `system_v1` estimated cost can be lower than ledger totals until graph-step cost rollup is tightened.
