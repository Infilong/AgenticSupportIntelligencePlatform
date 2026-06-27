# Model Settings Admin Surface

## Goal
Make model selection and token pricing an operational admin capability instead of hardcoded backend behavior.

## Audit Finding
The project already had a `ModelConfig` table, but the provider ignored it and always used static pricing from `DEFAULT_MODEL_PRICING`. That weakened the token-economy story and made the app feel less like a professional AI platform. Admins need to decide which model serves each purpose, inspect active routing, and verify the next AI run ledger records the selected provider, model, and cost profile.

## Changes Made
- Added workspace-scoped model configuration API:
  - `GET /api/v1/workspaces/{workspace_id}/model-configs`
  - `POST /api/v1/workspaces/{workspace_id}/model-configs`
  - `POST /api/v1/workspaces/{workspace_id}/model-configs/{model_config_id}/activate`
- Added `ModelConfigService` for list, create, activate, workspace isolation, and active pricing resolution.
- Updated `MockModelProvider` to resolve active workspace model config by purpose before estimating cost and writing `AIRun` records.
- Enforced active model `max_context_tokens` by recording a failed `AIRun` and raising a provider error when a request exceeds the configured context window.
- Extended the cost summary with model-level breakdown by provider/model.
- Added backend tests for create/list/activate, workspace isolation, active model config usage in provider cost/model recording, context-limit failure, and model-level cost summary.
- Added a frontend `Model settings` page where admins can create purpose-specific configs, activate configs, inspect active routing, and view pricing/context limits.
- Updated the frontend cost dashboard to show both by-purpose and by-model cost tables.

## Verification
- `uv run pytest -s tests/test_model_configs.py`
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run build`
- `npm run test`
- `uv run pytest -s tests/test_model_configs.py tests/test_ai_observability.py`
- `docker compose up -d --build api frontend`
- Live API smoke confirmed an active `classification` config changed the next run's classifier AI ledger entry to `mock-admin / mock-admin-classifier` with configured pricing.

## Current Evidence
Live smoke result:

```json
{
  "run_status": "completed",
  "route_decision": "finalize",
  "classifier_provider": "mock-admin",
  "classifier_model": "mock-admin-classifier",
  "classifier_cost": 0.00053
}
```

## Remaining Risks
- The provider is still a mock provider; a real OpenAI-compatible provider adapter is still needed.
- Context overflow currently raises a provider error; the graph should later convert this into a human-review route instead of surfacing a failed request.
- Role-based admin permissions are not implemented; workspace membership is still the authorization boundary.
- Context packing does not yet proactively shrink prompts to fit the configured model window before calling the provider.

## Next Recommended Ticket
Add real provider abstraction and graceful model-budget routing: keep tests on mock providers, introduce an OpenAI-compatible provider path, and route context-overflow cases to human review instead of surfacing a failed API request.
