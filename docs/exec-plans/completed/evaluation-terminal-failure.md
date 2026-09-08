# Explicit evaluation terminal failures
## Goal
Persist a failed evaluation outcome when unexpected execution/publication errors occur.
## Context
Evaluation creation commits running status before case execution. Unexpected failures currently
escape without a terminal update, so failed work looks active and cannot safely be deleted.
## Requirements
Preserve original exceptions and committed results/usage. Roll back unfinished writes, attempt
failed status with completion time, and emit content-free correlated failure diagnostics.
## Non-goals
Process-crash recovery, retries, lost commit acknowledgments or automatic model replay.
## Acceptance Criteria
Case and metrics failures persist failed status and retain usage. Failure-record persistence
errors do not mask the original exception. Success and permission behavior remain unchanged.
## Plan
1. Reproduce case/publication failures.
2. Extract completion/failure ownership from the oversized evaluator.
3. Verify failures, success, logs, related tests and live integration; lower source baseline.
## Verification
Mock-provider API regressions, persistence failure injection, affected backend suite and browser
integration. Preserve failing evidence and record remaining persistent-outage limits.
## Risks
Persistent database failure can prevent recording failed status; diagnostics must say so without
claiming recovery. Retain already committed accounting, never replay paid work automatically.
## Progress
2026-09-08: inspected execution lifecycle and added case/metrics failure reproductions.
Both failures reproduced. Extracted completion context and added secondary-persistence failure
coverage. Ruff and 32 affected tests pass; rebuilt API passes four browser checks and runtime
review shows 543 HTTP outcomes without server/errors. Lowered evaluator baseline to 479 lines.
Exact commands and artifacts: [testing](../../testing.md#evaluation-terminal-failures).
## Decisions
One focused execution context owns metric publication and unexpected-error finalization.
## Findings
Original unexpected failures left running status durable. The new boundary persists failed
status where storage allows; secondary failure is explicit and never replaces the original error.
## Final Result
Completed 2026-09-08 for in-process unexpected failures. Committed results/usage survive;
success and permission regressions pass. Process-crash and persistent-outage recovery remain open.
