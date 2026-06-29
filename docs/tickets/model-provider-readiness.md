# Model Provider Readiness Metadata

## Goal
Make model/provider settings operationally clear without storing or exposing secrets in the browser.

## Context
The backend already supports workspace model configs, active purpose routing, OpenAI/OpenAI-compatible execution, deterministic mock routing, AI run ledger records, and provider failure recording. The UI could infer some readiness from provider names, but the API did not explicitly tell admins whether a route was mock, live, missing credentials, archived, or only a custom placeholder integration.

## Requirements
- Expose non-secret readiness metadata on model config API responses.
- Do not expose API keys or secret values.
- Keep model configs workspace-scoped and permission-gated.
- Use the same response shape for list/create/activate and agent assigned-model summary.
- Show readiness and credential gaps in the Models page.

## Non-goals
- Do not implement browser-side API key storage.
- Do not add encrypted secret management in this ticket.
- Do not change provider execution behavior.
- Do not add network calls in tests.

## Design Plan
- Add derived `runtime_kind`, `credential_status`, and `readiness_label` fields to `ModelConfigResponse`.
- Compute readiness from provider, archive state, and backend `OPENAI_API_KEY` presence.
- Use a shared response helper for model-config routes and agent summaries.
- Update the Models UI to display ready routes and credential gaps.
- Add backend tests with `OPENAI_API_KEY` forced empty for deterministic missing-credential coverage.

## Files Changed
- `backend/app/schemas/model_config.py`
- `backend/app/api/v1/model_configs.py`
- `backend/app/api/v1/agents.py`
- `backend/tests/test_model_configs.py`
- `frontend/src/App.tsx`
- `frontend/tests/e2e/review-ux-smoke.spec.ts`
- `docs/tickets/model-provider-readiness.md`

## Test Plan
- `cd backend && uv run pytest -s -q tests/test_model_configs.py`
- `cd backend && uv run ruff check app/api/v1/agents.py app/api/v1/model_configs.py app/schemas/model_config.py tests/test_model_configs.py`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run build`
- `docker compose up -d --build api frontend`
- `make frontend-e2e-docker`

## Acceptance Criteria
- Mock model configs report `runtime_kind=mock` and `credential_status=not_required`.
- OpenAI configs without backend credentials report `runtime_kind=live` and `credential_status=missing`.
- The frontend Models page shows active credential gaps and per-config readiness labels.
- No secret value is returned by any model config response.

## Risks
- Readiness is an environment-derived signal, so tests must control `OPENAI_API_KEY` explicitly.
- Full secret management remains future work; this ticket only makes readiness honest.

## Human Review Checklist
- Open Models and create a mock config; confirm it shows no key required.
- Create an OpenAI config without setting `OPENAI_API_KEY`; confirm the route shows missing credentials.
- Confirm the UI never asks for or displays an API key.
- Run an agent with a missing live provider and verify the failure still appears in trace/cost ledger.

## Interview Notes
This shows mature platform design: provider configuration is not just a form. Operators get explicit readiness states, while secrets stay backend-only and model-call failures remain observable through the AI run ledger.
