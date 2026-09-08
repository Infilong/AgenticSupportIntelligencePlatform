# Stable graph execution order
## Goal
Preserve actual graph-step order when wall-clock timestamps tie or move backward.
## Context
The built-web verifier failed requested-language.spec.ts: the Auto trace starts with
classify_intent, then detect_language. The graph executes detection first, but get_trace sorts
only by created_at. Saved timestamps place classification before detection by about 96ms.
## Requirements
Persist execution order for new steps; use it for trace ordering and parent selection. Keep
workspace boundaries and concurrent persistence correct. Do not invent order for legacy history.
## Non-goals
Changing the language assertion, disabling concurrency, clock adjustment or durable graph resume.
## Acceptance Criteria
A deterministic backward-clock regression preserves language-first causal order. New persisted
step order is unique per run and safe on PostgreSQL. Existing/legacy traces remain readable.
The unchanged built-web browser suite passes through the reusable verifier.
## Plan
1. Inspect graph-step persistence, parent selection and trace readers; reproduce clock reversal.
2. Add a nullable sequence for legacy compatibility and explicit serialized ordering for new steps.
3. Migrate and test PostgreSQL ordering, failure paths and API compatibility.
4. Re-run the built-web verifier; preserve original failing artifacts and document legacy limits.
## Verification
Evidence: `.artifacts/built-web-68ed7c3cafd24484a4bdba5ed6a20833/` browser trace and logs.
Add tests forcing timestamps out of execution order; verify no assertions/retries are weakened.
## Risks
Historical timestamps cannot establish actual order after clock reversal. Backfilling guessed
order as fact would be misleading. Concurrency and parent-span assignment need one transaction.
## Progress
2026-09-08: real verifier failure inspected; current trace sort and latest-span lookup use timestamps.
2026-09-08 repair: deterministic backward/tied-clock tests both failed on the old implementation.
Added nullable sequence, unique/positive constraints and scoped PostgreSQL run locking in the
new graph_step_ordering service. Updated trace, latest-step and review-context readers.
Focused Ruff/API/PostgreSQL tests passed 62 cases; migration compatibility passed three cases.
Final legacy API/constraint coverage passed seven tests. The unchanged built-web suite passed
the original language-order assertion but failed another test waiting for an agent summary.
Its 26/27 result and pending network request are preserved in
`.artifacts/built-web-f0e4f8b7074f47e7b7de7a5f0c9b7ca2/`; diagnose before retrying.
The isolated API was rebuilt and readiness passed.
2026-09-08 acceptance: with metadata-only network diagnostics, the full built-web suite passed
27 tests in 41.2 seconds with unchanged assertions, concurrency and timeouts. Image/runtime
checks and cleanup passed; 1,810 HTTP outcomes had zero server/error outcomes. Evidence:
`.artifacts/built-web-087ce306cc784851a57751a258f1fd6e/`. The earlier editor stall remains
unexplained and is tracked in the production plan; this pass does not prove it repaired.
## Decisions
Repair persistence/read ordering rather than changing the language-selection test to hide the issue.
Sequence represents persisted order of the current serial graph. Legacy rows retain null and
timestamp/ID fallback; do not backfill guessed history. Downgrade refuses sequenced records.
Cross-run recency remains timestamp-based; this is not support for parallel graph branch causality.
## Findings
Auto trace timestamps: detect_language 22:56:40.392772Z; classify_intent 22:56:40.296552Z.
The original suite passed 26/27; migration and temporary-container cleanup passed.
## Final Result
Completed for serial graph sequencing, migration/legacy compatibility and browser acceptance.
Historical causal order remains unknown; parallel graph causality and durable resume remain
outside scope. Preserve the intermittent editor-stall evidence under the broader production plan.
