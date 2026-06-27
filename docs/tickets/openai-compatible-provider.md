# OpenAI-Compatible Provider Adapter

## Goal
Make the model-provider layer credible beyond deterministic mock demos by adding a real OpenAI-compatible chat-completions adapter while preserving mock-only automated tests.

## Context
The backend already uses LangGraph for support-agent orchestration and LangChain Core for prompt/runnable/parser composition. Before this ticket, graph nodes still instantiated the mock provider directly, which made active OpenAI model configs look cosmetic.

## Requirements
- Keep mock provider as the default for local demos and tests.
- Allow active model configs with `provider=openai` or `provider=openai-compatible` to use a real OpenAI-compatible HTTP adapter.
- Read provider credentials from environment, not from the database or frontend.
- Record every live success or failure as an `AIRun` row with provider, model, purpose, tokens, estimated cost, latency, status, and error message.
- Route provider failures through the existing graph failure and human-review path.
- Do not make automated tests call external model APIs.

## Design
- `ConfiguredModelProvider` resolves the active `ModelConfig` for a purpose and dispatches to either the mock provider or `OpenAICompatibleModelProvider`.
- `OpenAICompatibleModelProvider` calls an OpenAI-compatible `/chat/completions` endpoint through an injectable transport.
- Tests use a fake transport to prove success and failure ledger behavior without network calls.
- The frontend model settings panel now exposes provider choices: mock, OpenAI, and OpenAI-compatible.

## Environment
- `OPENAI_API_KEY`: required only when an active config uses `openai` or `openai-compatible`.
- `OPENAI_BASE_URL`: defaults to `https://api.openai.com/v1`.
- `OPENAI_TIMEOUT_SECONDS`: defaults to `30`.

## Verification
- `uv run pytest -s tests/test_model_configs.py`
- `uv run ruff check .`
- Full backend/frontend validation should run before committing.

## Risks
- The app still uses approximate local token estimation unless the provider response includes usage metadata.
- Chat-completions formatting is deliberately simple: the LangChain prompt is sent as one user message. A future ticket can split system/human messages more precisely.
- Real API keys are intentionally not stored in workspace settings; this is safer for a local portfolio project but less convenient than a secrets manager.

## Interview Notes
Explain that tests never depend on paid model calls. The production path is still real: active model configs route through a provider adapter, all outcomes are ledgered, and failures are visible in trace/human review instead of being hidden.
