# Trace And Review Workbench Redesign

## Goal
Make the most technical/admin-heavy pages feel like professional tools instead of raw demo views.

## Audit Findings
- Human review used one shared decision/editor control for every pending item, which is unsafe and confusing for real reviewers.
- Pending review rows did not clearly separate guardrail reasons, proposed answer, reviewer decision, and reviewer notes.
- Trace view displayed raw JSON as the primary experience, making users read implementation state instead of understanding the workflow.
- Tool calls, model calls, route decisions, citations, confidence, and no-source state were present but not visually promoted.

## Changes Made
- Added per-review draft state, so each pending review has its own decision, edited answer, and reviewer note.
- Added row-level review resolution actions and trace inspection that loads the target graph run.
- Added a review policy sidebar with the review triggers this system currently handles.
- Rebuilt trace display as a workbench with run context, graph health, model/tool call counts, latency, token/cost totals, and readable state signals.
- Preserved raw input/output JSON behind drill-down details for developer debugging.

## Verification
- `npm run test`
- `npm run build`
- `docker compose up -d --build frontend`

## Remaining Risks
- `frontend/src/App.tsx` is still too large. The trace and review components should be extracted into feature modules.
- Trace data would be stronger if the backend exposed guardrail results and AI run details directly in the trace response.
- Review actions still rely on free-text comments rather than structured review rubrics.

## Next Recommended Ticket
Expose AI run ledger details and guardrail results in the trace API, then render model, prompt tokens, completion tokens, estimated cost, guardrail severity, and prompt template version inline in the trace workbench.
