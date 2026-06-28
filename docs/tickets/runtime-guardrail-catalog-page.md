# Runtime Guardrail Catalog Page

Date: 2026-06-28

## Goal
Make guardrails and governance a first-class product area instead of only showing guardrail results inside traces and review details. Developers and admins should be able to inspect active runtime guardrails, pass/fail history, severity, action on failure, and trace links from a dedicated page.

## Context
The professional platform objective requires visible and configurable guardrails. The app already persisted `GuardrailResult` rows after LangGraph runs, but there was no workspace-scoped API or navigation page for guardrails. A full editable policy registry is still future work, so this ticket implements an honest runtime-backed catalog using actual guardrail definitions and persisted results.

## Implementation
- Added `app/schemas/guardrail.py` response models.
- Added `GuardrailCatalogService` with runtime guardrail definitions for:
  - prompt injection
  - citation required
  - unsupported answer
  - confidence threshold
  - language preservation
  - model provider failure
  - token budget failure
- Added `GET /api/v1/workspaces/{workspace_id}/guardrails`.
- Aggregated per-workspace evaluations, failures, pass rate, last failure, and recent failed results from `GuardrailResult` rows.
- Added focused tests proving guardrail failures are populated by real agent runs and isolated by workspace.
- Added Guardrails to frontend navigation and readiness.
- Added a Guardrails page showing policy purpose, stage, severity, action on fail, configurable/fixed status, metrics, and recent failures linked to traces.

## Backend/API Impact
The new endpoint is read-only and workspace-scoped through `require_workspace_member`. It does not mutate guardrail policy configuration. The response is based on runtime definitions and persisted guardrail results, so it does not fake editable governance.

## Validation
- `uv run ruff check .` passed.
- `uv run pytest tests/test_guardrails.py -q -s` passed: 2 tests.
- `uv run pytest -q -s` passed: 101 tests.
- `npm run test -- --run` passed.
- `npm run build` passed.

## Manual Review Checklist
- Open the Guardrails page from the sidebar.
- Confirm guardrails are visible before any run history.
- Run a no-source or prompt-injection style agent request.
- Confirm failed guardrails appear with severity and trace links.
- Confirm another workspace does not see the first workspace's guardrail history.

## Risks and Tradeoffs
- This is not a full editable policy registry yet. It is a runtime-backed governance catalog and failure dashboard.
- Some objective guardrail categories, such as unsafe tool-call blocking and output schema validation, are not implemented as runtime guardrails yet and are therefore not shown as active policies.
- Configurable flags identify where settings already influence behavior, such as confidence threshold and token budget, but there is no central policy editor yet.

## Interview Notes
This ticket is useful for explaining honest platform maturity. The page elevates guardrails to a first-class product area while preserving backend truth: active policies are derived from implemented runtime checks and persisted `GuardrailResult` rows, not placeholder UI.
