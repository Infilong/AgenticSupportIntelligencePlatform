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
- Added backend tests for create/list/activate, workspace isolation, and active model config usage in provider cost/model recording.
- Added a frontend `Model settings` page where admins can create purpose-specific configs, activate configs, inspect active routing, and view pricing/context limits.

## Verification
- `uv run pytest -s tests/test_model_configs.py`
- `uv run ruff check .`
- `uv run pytest -s`
- `npm run build`
- `npm run test`
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
- `max_context_tokens` is recorded in config but not yet enforced in provider/context packing.
- Role-based admin permissions are not implemented; workspace membership is still the authorization boundary.
- The cost dashboard does not yet break down cost by configured model.

## Next Recommended Ticket
Add real provider abstraction and model-config enforcement: keep tests on mock providers, but introduce an OpenAI-compatible provider path, enforce `max_context_tokens`, and show model-level cost breakdown in the cost dashboard.
