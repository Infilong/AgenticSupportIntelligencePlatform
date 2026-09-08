# Client-visible failure references
## Goal
Let users report unexpected failures with a safe reference that joins server logs.
## Context
Initial reproduction: unhandled 500 responses lost the middleware's response header and CORS
did not expose request IDs. The current implementation addresses these paths; see Progress.
## Requirements
Generic JSON error with server request ID, exact configured origin policy, no exception details.
Browser 5xx feedback includes a valid reference and preserves session/draft; no automatic replay.
## Non-goals
Global server-log sanitization, stack-trace suppression, retry/idempotency redesign.
## Acceptance Criteria
Unhandled error response and HTTP log share an ID; untrusted origins remain disallowed.
Normal/handled CORS replies expose the header. Browser failure/retry retains user input.
## Plan
1. Reproduce missing references and CORS exposure with real application middleware.
2. Add safe error response handling and validated reference display in the HTTP client.
3. Verify backend errors/origins, browser recovery and existing session behavior.
## Verification
Mocked failure tests, existing logging/authorization checks and browser mutation recovery.
## Risks
Server error handling sits outside normal CORS; apply the same origin policy without exposing
private exception messages. Existing 401 rejection semantics must remain unchanged.
## Progress
2026-09-08 inspected middleware and HTTP client; added missing-reference regressions.

2026-09-08 documentation-only continuation: inspected current handler/client/tests and saved
logs. The initial five failures are preserved. Backend lint and 24 affected tests pass in
15.35s; frontend build/types pass; the full browser suite passes 27 tests in 57.7s. Browser
500 injection and real API retry are distinct from backend handler/CORS verification.
Exact commands, evidence and limits live in [testing](../../testing.md#client-visible-error-references).
No application code or application tests were changed or rerun during this audit.
Next implementation continuation: review the complete feature diff and runtime evidence,
resolve any findings, then move this plan to completed and update inbound links. The broader
production plan remains active; do not infer global logging or recovery guarantees.
## Decisions
2026-09-08 final review: the handler preserves the original exception for server reporting and
sets no-store on unexpected-error responses. Added regression assertions for both contracts.
Ruff and 25 affected tests pass in 16.20s (`final-review-backend.log`); the existing complete
browser run remains 27 passes and no application code changed after it. Retained runtime logs
contain 2,525 HTTP outcomes with zero server/error outcomes (`final-review-summary.json`).
Reviewed handler/middleware ordering, origin policy, UUID display, authorization and session
behavior. No unresolved P0/P1 finding within this feature. All acceptance criteria are met.

Show references only for server failures; keep existing validation/permission messages intact.
## Findings
The logger retains request ID on exceptions, but the default outer server error response does not.
## Final Result
Completed 2026-09-08 after final review and regression verification. Unexpected errors provide
safe log-correlated references; configured origins can read them and browser retries preserve
draft/session state. Global log sanitization, streaming failures after response start, durable
recovery and ambiguous commit acknowledgments remain outside this focused feature.
