# Guardrail Routing Decision Records

## Goal
Make routing guardrails first-class trace evidence instead of only catalog labels or hidden route reasons.

## Context
The guardrail catalog already listed `privacy_complaint`, `high_safety_risk`, and `escalation_needed`, and the LangGraph routing step used those signals to send runs to human review. However, the runtime guardrail evaluator did not persist individual `GuardrailResult` records for those policies, which weakened traceability and made the guardrail catalog less honest.

## Requirements
- Store pass/fail guardrail decisions for privacy complaint classification.
- Store pass/fail guardrail decisions for high safety risk classification.
- Store pass/fail guardrail decisions for escalation-needed classification.
- Respect existing effective guardrail policy settings, including disabled policies and record-only actions.
- Surface failures through the existing trace and guardrail catalog APIs.

## Non-goals
- Do not add a new guardrail model.
- Do not add a new policy type beyond the existing catalog entries.
- Do not change classification behavior.
- Do not change human review resolution behavior.

## Design Plan
- Extend `evaluate_guardrails()` to append decisions from `intent`, `safety_risk`, and `escalation_needed` state.
- Use the existing `_append_decision()` helper so workspace policy overrides continue to apply.
- Add an integration test that runs a Chinese privacy complaint and proves the three routing guardrails are recorded in both trace and catalog.

## Files Changed
- `backend/app/services/guardrails.py`
- `backend/tests/test_guardrails.py`
- `docs/tickets/guardrail-routing-decision-records.md`

## Test Plan
- `cd backend && uv run pytest -q tests/test_guardrails.py`
- `cd backend && uv run ruff check app/services/guardrails.py tests/test_guardrails.py`

## Acceptance Criteria
- Privacy complaint runs have a failed `privacy_complaint` guardrail result.
- High safety risk runs have a failed `high_safety_risk` guardrail result.
- Escalation-needed runs have a failed `escalation_needed` guardrail result.
- Trace API exposes those decisions with graph step IDs.
- Guardrail catalog usage and recent failures include those decisions.

## Risks
- Catalog definitions and runtime decisions can drift if future guardrails are added only to one side.
- Low-risk passing decisions add more guardrail rows per run, but this is acceptable because traceability is a product requirement.

## Human Review Checklist
- Run a privacy complaint demo message and inspect the trace guardrail section.
- Confirm the Guardrails page shows recent failures for Privacy complaint, High safety risk, and Escalation needed.
- Confirm policy disable/record-only behavior still works for configurable guardrails.

## Interview Notes
This demonstrates an important AI platform principle: if a policy affects routing, it must be persisted as inspectable evidence, not just implemented as an invisible branch condition.
