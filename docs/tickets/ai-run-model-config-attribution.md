# AI Run Model Config Attribution

## Goal
Persist the exact `ModelConfig` route that produced each `AIRun`, then expose that route in trace and cost views. This closes the gap where provider/model strings were visible but the platform could not prove which workspace or agent model config caused the call.

## Context
The product goal requires professional cost/token/model observability. Previous work added model configs, agent-level model routing, prompt version linkage, and a trace runtime decision board. The remaining weakness was that `AIRun` stored provider/model/purpose but not the resolved `model_config_id`. That made model routing harder to audit after configs were archived, replaced, or assigned at agent level.

## Requirements
- Add nullable `AIRun.model_config_id` with `SET NULL` behavior for historical ledger rows.
- Carry the resolved model config id through pricing resolution into every mock/OpenAI-compatible model provider success and failure path.
- Preserve fallback behavior for default mock pricing by storing `null` when no model config exists.
- Expose `model_config_id` in trace AI run responses and recent cost ledger responses.
- Show route source in the trace AI run panel and cost recent ledger.
- Prove storage and API serialization with tests.

## Non-Goals
- Do not change model config activation or archive semantics.
- Do not hard-delete historical AI runs.
- Do not add provider secrets or real paid model calls to tests.
- Do not redesign the full trace or cost pages.

## Implementation
- Added Alembic migration `0017_ai_run_model_config_attribution`.
- Added `AIRun.model_config_id` and a relationship to `ModelConfig`.
- Extended `ModelPricing` to carry `model_config_id`.
- Updated `ModelConfigService.resolve_pricing()` to include the resolved config id.
- Updated `MockModelProvider` and `OpenAICompatibleModelProvider` to record the resolved config id on all `AIRun` rows, including failures.
- Extended `AIRunTraceResponse` and `RecentAIRunSummaryResponse`.
- Updated frontend trace/cost types and route-source labels.
- Updated `docs/database-schema.md`.

## Validation
Passed:
- `cd backend && uv run ruff check app/models/ai.py app/services/token_accounting.py app/services/model_config_service.py app/services/model_provider.py app/services/cost_service.py app/api/v1/costs.py app/schemas/agent.py app/schemas/costs.py tests/test_agents.py tests/test_model_configs.py tests/test_ai_observability.py`
- `cd backend && uv run pytest -s -q tests/test_model_configs.py::test_active_model_config_controls_provider_pricing_and_ai_run tests/test_agents.py::test_agent_model_config_assignment_drives_ai_run_provider_and_summary tests/test_ai_observability.py::test_cost_summary_counts_failed_ai_runs`
- `cd backend && uv run pytest -s -q tests/test_model_configs.py tests/test_agents.py::test_support_agent_run_persists_trace_tool_calls_and_ai_runs tests/test_agents.py::test_agent_model_config_assignment_drives_ai_run_provider_and_summary tests/test_ai_observability.py tests/test_budget_policies.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`

Attempted but blocked by WSL browser dependency:
- `cd frontend && npm run test:e2e` failed before app load because Playwright Chromium could not start: `libnspr4.so: cannot open shared object file`.

## Human Review Checklist
- Confirm that historical/fallback AI runs showing `model_config_id: null` is acceptable.
- Confirm trace and cost wording is clear enough: `model config <id>` versus `default pricing fallback`.
- Confirm whether WSL browser dependencies should be installed so Playwright can run in this environment.

## Interview Notes
This ticket demonstrates auditability beyond surface UI. The platform now records not only provider and model strings, but also the workspace-scoped model config route that selected pricing/context behavior. That matters for cost investigations, model migrations, archived configs, and explaining why a production agent used a specific model.
