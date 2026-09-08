# Workspace response isolation

## Goal
Prevent delayed requests from a previous workspace or session from populating current UI state.
## Context
AppShell owns workspace selection and most resource state. Async loaders write state after
awaiting responses without checking whether the active scope changed.
## Requirements
Separate UI lifetime by authenticated session and workspace. Reject stale callbacks that change
outer selection. Preserve navigation and explicit creation feedback; backend authorization remains
authoritative. Switching scope clears resource drafts rather than transferring protected content.
## Non-goals
Canceling already-dispatched backend work, replacing the shell, or adding a URL router.
## Acceptance Criteria
A delayed A response released after selecting B cannot replace B's documents. Logout/session
changes cannot revive previous data. Existing complete browser workflows continue to pass.
## Plan
1. Reproduce the delayed-response failure in Playwright against the isolated live API.
2. Put session/workspace identity and navigation in a small root boundary; key the scoped shell
   and guard parent callbacks by a monotonically changing scope generation.
3. Verify scope transitions and existing browser journeys, build, then update evidence/guides.
## Verification
Focused delayed-response regression before/after; full Chromium suite, frontend build,
documentation/source-size gates and diff review. Save logs under .artifacts/workspace-isolation/.
## Risks
Remounting resets drafts and may drop operation notices. Stale callbacks must not restore an
old selection, including A-to-B-to-A transitions. A request can still finish in its original
workspace after a UI switch; this repair must not imply server-side cancellation.
## Progress
2026-09-08: inspected current selection, auth persistence, loaders and browser acceptance.
Reproduced workspace A documents replacing B after releasing the delayed response. Root App now
owns persisted session, selection and navigation; a generation-keyed shell clears resource state
and rejects stale callbacks. Scope creation/leave/delete retain transition feedback.
Final verification: all 15 Chromium tests pass (49.4s), including three new scope/session/return
visit cases; build/type checks, 17 tooling tests, documentation/size gates and diff check pass.
Runtime window: 3,529 HTTP outcome records, zero server/error-type matches; mock embeddings and
absence of provider credentials verified. See [testing](../../testing.md#workspace-response-isolation)
for retained artifacts and earlier failures.
## Decisions
Use one owner for this coupled frontend boundary. Do not expand the legacy oversized shell.
## Findings
The existing reconciliation panel already keys its local state by session/workspace; other
shell-owned resources lacked that protection before this repair.
The first regression observed too early and passed before the delayed React update. Settling
windows exposed the actual A-over-B failure. The first broad post-fix run passed 13 tests but
the new session test used an ambiguous Login selector; it now targets the submit button.
## Final Result
Completed 2026-09-08. Delayed data and parent callbacks cannot cross the tested UI scope
transitions; drafts reset and allowed navigation remains. The shell shrank from 8,067 to 8,061
lines, with the baseline lowered. Backend cancellation, full permission coverage and production
readiness are not claimed. The broader production plan remains active.
