# Guardrail Governance Board

## Goal
Make the Guardrails page scale like a professional governance console. Admins and AI engineers should be able to filter implemented runtime policies, search by policy/stage/action/node, and read product-friendly action labels without losing access to trace-backed failures.

## Context
The backend already exposes a workspace-scoped guardrail catalog with real runtime definitions, effective policies, usage metrics, and recent failed guardrail results. The previous UI showed every policy as a card, but it did not provide policy filters/search and still surfaced raw action codes such as `route_to_human_review`.

## Requirements
- Keep the page backed by the existing `/guardrails` catalog.
- Add filter modes for all policies, failed policies, configurable policies, fixed policies, and policies that route to human review.
- Add search over policy label, description, guardrail type, stage, action, severity, and related workflow nodes.
- Use friendly visible labels for guardrail stages and failure actions.
- Fix the duplicate `Configurable` metric in the summary grid.
- Add browser coverage for the filter/search focus path and friendly action label.

## Non-goals
- No backend schema change.
- No new guardrail policies.
- No claim that deterministic v1 guardrails are comprehensive safety governance.

## Implementation Notes
- Added `GuardrailView` state and view options.
- Added a `Governance policy board` toolbar with segmented filters, search, and routing-policy count.
- Added `friendlyGuardrailAction`, `friendlyGuardrailStage`, and `guardrailMatchesView` helpers.
- Replaced visible raw action code with product language while preserving API-backed values in state.
- Corrected the repeated summary metric from duplicate `Configurable` to `Fixed`.

## Verification
- `cd frontend && npm test -- --run` - typecheck passed.
- `cd frontend && npm run build` - production build passed.
- `docker compose up -d --build frontend` - rebuilt the local browser target.
- `make frontend-e2e-docker` - first run caught an ambiguous `Prompt injection` locator; after tightening the assertion to the policy heading, the Playwright smoke test passed.

## Human Review Checklist
- Confirm the Guardrails page is easier to scan with many policies.
- Confirm fixed safety policies still appear non-editable.
- Confirm configurable policies retain owner-gated controls.
- Confirm raw backend codes are not the main visible admin language.
