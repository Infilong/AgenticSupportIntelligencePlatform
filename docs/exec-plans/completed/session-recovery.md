# Session recovery

## Goal
Make invalid/expired session and initial account-loading failures explicit and recoverable.
## Context
The root now isolates scope generations, but AppShell starts account/workspace requests without
rejection handlers. The HTTP transport discards status, so authentication failure cannot trigger
a safe session transition.
## Requirements
Clear only the current rejected authenticated session on 401; retain sessions on 403/network/5xx.
Show an actionable sign-in notice, allow bootstrap retries, and handle background rejections.
## Non-goals
Token refresh, cross-tab synchronization, changing backend JWT semantics, or automatic mutation retries.
## Acceptance Criteria
Invalid saved credentials return to login without uncaught errors. Transient bootstrap failure
remains visible and a manual retry recovers. Forbidden requests do not log users out. Existing
multilingual and workspace-isolation browser tests pass.
## Plan
1. Reproduce invalid-token startup with a real API response.
2. Extract typed HTTP transport and bind authentication failure to the root generation.
3. Handle rejected background loads and provide account bootstrap retry; verify browser boundaries.
## Verification
Focused failure regressions, full Chromium suite, frontend build/type checking, source/doc gates,
tooling tests and diff review. Retain .artifacts/session-recovery/ evidence.
## Risks
A late 401 must not clear a newer session. A wrong-password login is not expiration. Never treat
permission denial or a temporary network failure as logout; never replay a failed mutation.
## Progress
2026-09-08: inspected current root, transport, bootstrap effects and backend 401 contract.
Reproduced invalid saved-token startup. Extracted typed transport, bound authenticated rejection
to the root generation, handled discarded read promises and enabled Refresh before workspace
selection. Final full Chromium suite: 22 passed in 51.1s. Build/type checking, 17 tooling tests,
documentation/source-size gates and whitespace review pass. Captured API window: 2,506 outcomes,
zero server failures; mock embeddings and no provider key verified. See
[testing](../../testing.md#session-recovery) for commands and preserved failed evidence.
## Decisions
Keep transport and scope lifetime separate; preserve backend-owned authentication and permissions.
## Findings
At initial inspection, account/workspace startup promises had no rejection handlers.
The first focused post-fix run exposed Refresh's disabled state when bootstrap failed before
workspace selection. Four tests passed; that recovery test failed. Enabling bootstrap retry
resolved it; the final suite also covers network failure and wrong-password recovery.
## Final Result
Completed 2026-09-08. Seven browser regressions cover saved invalid token, bootstrap 503/network
failure, protected 401/403, late old-scope 401 and corrected login retry. Session expiration
clears scoped drafts; 403 and transient failures preserve them. No automatic mutation retries,
token-refresh implementation or complete authorization coverage is claimed. AppShell shrank
from 8,061 to 8,041 lines; the baseline was lowered. The production goal remains active.
