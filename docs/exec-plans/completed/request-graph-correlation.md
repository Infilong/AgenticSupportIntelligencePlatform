# HTTP request and graph correlation
## Goal
Let an operator find the persisted graph run associated with an HTTP request, including failures.
## Context
HTTP outcome logs have request IDs; graph/retrieval/model records have graph IDs but no log link.
## Requirements
Server-generated request identity; event after graph persistence; safe structured fields only;
correct request isolation across synchronous workers and cleanup on failure.
## Non-goals
Full OpenTelemetry, durable background propagation, global log redaction, changing API permissions.
## Acceptance Criteria
Real agent requests produce an event linking response request ID to persisted graph/trace IDs.
Failed execution retains the link; denied requests create none. Parallel requests never share IDs.
Events contain no customer text, credentials, raw paths or exception messages.
## Plan
1. Add a request-local identity context and structured workflow event helper.
2. Emit after run creation; verify real API success/failure/denial and concurrent context isolation.
3. Rebuild, inspect live logs/traces and document limits.
## Verification
Mock-provider API tests, concurrent middleware tests, relevant logging/graph suites and browser smoke.
## Risks
Context must reset even on exceptions; thread-worker propagation must be tested. Keep event
cardinality one per created run, not unbounded metadata arrays. No migration or paid calls.
## Progress
2026-09-08 inspected logger middleware, run persistence and failure tests; added scoped context
and event emission after GraphRun persistence. One implementation owner across these boundaries.
## Decisions
Use a separate event per graph so multi-case system evaluations can share one request ID
without accumulating graph arrays in the HTTP outcome log.
## Findings
Direct service work outside HTTP has no request ID; do not fabricate a correlation identifier.
## Final Result
Completed 2026-09-08: structured correlation after run persistence, concurrent request isolation,
cleanup and multi-case linkage pass 29 affected tests with PostgreSQL enabled and backend lint.
Seven browser checks pass. All 18 live graph events join HTTP outcomes and match persisted
graph/trace IDs; 591 HTTP outcomes have no server/error outcomes. Repository gates pass.
See [evidence](../../testing.md#http-request-to-graph-correlation). Graphless/distributed calls,
global log redaction and graph recovery remain separate requirements.
