# Preserve agent edits during background loading

## Evidence
On 2026-09-07, repeated Chromium execution failed twice at the agent-name assertion in
`frontend/tests/e2e/review-ux-smoke.spec.ts`. The expected name was
`E2E Support Agent Updated`; observed text included the old name prepended to the new name.
Traces and screenshots are retained in `.artifacts/20260907-clock-fix/`.

`AppShell.loadAgents` reapplies controls on every list response. Entering the agent tab starts
another list request even if an agent is already displayed. A late response can therefore
replace a draft while it is being edited. The current smoke test must keep its typing and
focus assertions; waiting for loading to finish would hide the user-facing defect.

## Bounded implementation plan
1. Add a deterministic browser regression that holds the agent-list response, edits a control,
   then releases the response and proves the draft survives.
2. Extract control draft initialization and edit tracking into a small feature hook. Keep
   rendering and transport in their existing locations for this ticket. Do not grow AppShell.
3. Reset drafts only for an explicit agent/workspace selection or successful save; ignore
   stale responses belonging to a prior selection. Define refresh behavior for clean drafts.
4. Verify agent switching, workspace switching, successful save, failure retention, and the
   existing focus journey. No backend/database contract changes are required.

## Acceptance
Delayed list responses preserve unsaved controls, switching selects the correct saved values,
and repeated browser runs pass. Lower AppShell's size baseline if extraction shrinks it.
Record successful evidence alongside the original failures and update the active loop.

## Implemented and verified
The draft hook now owns initialization, edits and list-request generations. Dirty same-agent
refreshes preserve controls; explicit selection/save invalidates older list requests. Workspace
changes reset draft context and reject callbacks captured in an earlier workspace.
AppShell shrank from 8111 to 8100 lines; its baseline was lowered.

The browser regression fails against the original shell and passes with the repair. Final
repeat run: 9/9 passed in `.artifacts/20260907-agent-draft-final/`, including failed-save draft
retention and successful retry. Production build and source-size check passed. See
[testing](../testing.md) for intermediate failures and [learning notes](../learning/async-editor-drafts.md)
for the ownership tradeoff.

Explicit agent/workspace switching with delayed responses still needs dedicated coverage.
Summary/workflow response ordering remains outside this draft-control repair. Do not use this
passing regression to claim all frontend async state is protected.
