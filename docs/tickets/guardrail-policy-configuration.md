# Guardrail Policy Configuration

## Goal
Add backend-supported workspace guardrail policy controls so owners can configure supported review-routing guardrails without turning the Guardrails page into a fake UI.

## Scope
- Added a persisted `guardrail_policies` table.
- Added owner-only `PATCH /api/v1/workspaces/{workspace_id}/guardrails/{guardrail_type}/policy`.
- Extended the guardrail catalog response with effective policy values: enabled state, severity, action on fail, and optional threshold.
- Made LangGraph routing read effective guardrail policies before adding route reasons.
- Made post-run guardrail evaluation read the same policies before storing `GuardrailResult` rows.
- Added frontend Guardrails policy controls with explicit Save buttons.
- Added Settings shortcut to Guardrail policies.

## Important Design Decisions
- Fixed safety guardrails such as `prompt_injection`, `privacy_complaint`, `high_safety_risk`, and `model_provider_failure` are visible but not configurable.
- Configurable guardrails include `citation_required`, `unsupported_answer`, `confidence_threshold`, `language_preservation`, `model_budget_failure`, and `escalation_needed`.
- `record_only` keeps evaluation visibility but does not route a failed configurable policy to human review.
- Confidence threshold precedence is: explicit workspace guardrail policy threshold first, otherwise agent runtime confidence threshold, otherwise default `0.5`.
- Disabling one configurable policy does not disable other protections. For example, disabling `citation_required` still allows `unsupported_answer` to route unsafe no-source runs to review.

## Folder / Growing Resource UI Note
The current codebase already supports folder-scoped resource management for growing uploaded resources:
- backend `ResourceFolderService` supports `knowledge_document` and `dataset` folders;
- knowledge documents can be uploaded, edited/reindexed, moved, and deleted;
- datasets can be imported, moved, and deleted;
- destructive actions and folder management are owner-gated;
- frontend document and dataset panels show folder filters, scoped search, move controls, delete controls, and empty-folder deletion.

This satisfies the current requirement that file-name-heavy areas should not become unbounded flat lists. Future file-like resource types should reuse the same folder pattern instead of adding standalone flat upload panels.

## Tests Added
- Owner can update guardrail policy and catalog shows effective values.
- Member cannot update guardrail policy.
- Fixed guardrails cannot be configured.
- Unknown guardrail policy update returns not found.
- Disabled citation policy is removed from route reasons and persisted guardrail results while other protections remain active.

## Validation
- `cd backend && uv run pytest tests/test_guardrails.py -q -s` -> 5 passed.
- `cd backend && uv run ruff check .` -> passed.
- `cd backend && uv run pytest -q -s` -> 129 passed.
- `cd frontend && npm run typecheck` -> passed.
- `cd frontend && npm run build` -> passed.

## Human Review Checklist
- Confirm fixed guardrails should remain non-configurable.
- Confirm `record_only` is an acceptable owner-only action for supported configurable guardrails.
- Open Guardrails page and verify policy controls are understandable.
- Run a no-source message after disabling `citation_required` and confirm review routing still happens through `unsupported_answer`.

## Next Recommended Ticket
Continue frontend UX cleanup around input stability and review-page clarity. The next ticket should audit text inputs/textarea focus behavior and simplify the human review page so pending work is visually obvious.
