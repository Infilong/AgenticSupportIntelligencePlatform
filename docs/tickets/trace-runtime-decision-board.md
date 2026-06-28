# Trace Runtime Decision Board

## Goal
Make the trace workbench explain model and prompt decisions without forcing developers to read raw AI run JSON. A technical user should quickly see which model purposes ran, which prompt templates and versions were used, where token/cost pressure came from, and whether provider calls failed.

## Context
The backend already returns trace AI run ledger rows with provider, model, purpose, tokens, cost, cache hit, prompt template name/text, prompt version, and status. Prior tickets linked AI runs to graph steps and prompt templates. The remaining UI gap was that this data appeared mostly inside individual step panels, so the overall runtime decision story was harder to scan.

## Requirements
- Use only existing `GraphTrace` API data.
- Add a trace-level model/prompt operations board.
- Summarize AI runs by purpose, provider/model, call count, failures, tokens, cost, and latency.
- Summarize prompt template/version usage and prompt-token pressure.
- Show prompt coverage and cache behavior at trace level.
- Preserve existing per-step AI run details and prompt source drilldowns.
- Add browser coverage against a real trace generated through the backend API.

## Non-goals
- No database migration.
- No new model config id persisted on `AIRun` in this ticket.
- No change to provider routing behavior.
- No fake prompt/model metadata.

## Implementation Notes
- Added `summarizeAIRunPurposes` and `summarizePromptTemplates` helpers.
- Added a `Model and prompt decisions` board to `TraceViewer`.
- Added summary cards for prompt coverage, top cost call, and cache behavior.
- Added purpose-route cards and prompt-version cards backed by `trace.ai_runs`.
- Extended Playwright smoke coverage to assert the board appears on a real review-routed trace.

## Verification
- `cd frontend && npm test -- --run` passed.
- `cd frontend && npm run build` passed.
- `docker compose up -d --build frontend` rebuilt and restarted the composed frontend/API stack.
- `make frontend-e2e-docker` passed, including a real review-routed trace opening and assertions for the trace runtime decision board, Data/Knowledge folder search focus, Evaluation board search/selection, Tools search focus, Guardrail search focus, and human-review editor focus.

## Human Review Checklist
- Confirm Trace now explains model/prompt behavior before raw JSON.
- Confirm the board remains honest when prompt templates are missing or calls are unversioned.
- Confirm per-step AI run details still expose prompt source and errors.
- Confirm this is enough for interview explanation without claiming model config ids are persisted per `AIRun`.
