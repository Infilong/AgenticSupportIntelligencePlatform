# Trace Context Packing UX

## Goal
Make the new `compress_context` LangGraph node understandable in the Trace page without requiring users to open raw JSON.

## Context
The backend now records context packing as a dedicated graph step. The Trace UI already showed generic output signals and raw payloads, but a professional AI platform should make token-economy decisions visible as an operational signal: what context was packed, whether chunks were trimmed, what token pressure existed, and which model/context limit was used.

## Change Made
Added a dedicated `Context packing` panel to trace step inspection and timeline cards when a selected step exposes `token_budget_action`.

The panel shows backend-provided values only:

- token budget action;
- packed chunk count;
- packed citation count;
- planned token count;
- context limit;
- token pressure percentage;
- planning model.

Checkpoint cards now distinguish retrieved chunks from packed chunks. This makes it clear that retrieval and model-context packing are separate workflow responsibilities.

## Files Changed
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/tests/e2e/review-ux-smoke.spec.ts`

## Design Reasoning
The panel is intentionally simple, monochrome, and information-dense. It does not add decorative UI or fake metrics. It turns existing trace state into a readable operator surface for developers and admins debugging token usage.

## Validation
Validated in this ticket:

- `cd frontend && npm run build` -> passed.
- `cd frontend && npm run typecheck` -> passed.
- `docker compose up -d --build frontend` -> passed and refreshed running API/frontend containers.
- First `make frontend-e2e-docker` run exposed an overly specific assertion against `No context`; the live trace packed context successfully.
- Updated the smoke assertion to verify stable context-packing panel fields.
- `make frontend-e2e-docker` -> 2 passed.

## Human Review Checklist
- Open Runs & traces and load a run.
- Select `Compress Context` in the execution navigator.
- Confirm the context-packing panel shows token plan, context limit, packed chunks, packed citations, and pressure.
- Confirm retrieved evidence still appears separately when chunks are present.
- Confirm checkpoint cards show both retrieved and packed counts.

## Interview Notes
This is an example of turning backend traceability into useful product UX. The system does not merely store token-budget decisions; it makes them visible as part of the stateful agent workflow so engineers can explain and debug cost-control behavior.
