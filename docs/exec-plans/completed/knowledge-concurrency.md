# Concurrent knowledge mutations
## Goal
Serialize same-document reindexing so committed versions and document metadata remain correct.
## Context
Version allocation reads MAX(version) before publication. Concurrent sessions can compute the
same next version; cached document attributes can hide a competing committed change.
## Requirements
Workspace-scoped locking, fresh state after lock acquisition, no duplicate version allocation,
unchanged audit/usage and permission contracts. Move/delete share the same mutation boundary.
## Non-goals
Durable job queues, lock-free indexing, crash recovery, folder assignment/deletion races.
## Acceptance Criteria
Controlled PostgreSQL overlap yields two successful ordered versions and preserves newer
metadata when the later request omits it. Existing atomicity and accounting checks remain green.
## Plan
1. Reproduce overlapping version allocation with blocked provider and real PostgreSQL lock evidence.
2. Lock and refresh the scoped document before mutation/next-version reads.
3. Verify concurrency, audit rollback, provider accounting, permissions and browser integration.
## Verification
PostgreSQL synchronized overlap, affected pytest and Ruff, browser journeys, repository gates.
## Risks
Document lock spans bounded provider I/O. Use NO KEY UPDATE so child-row foreign key checks
remain compatible; independent embedding ledger uses workspace locks, not document locks.
## Progress
2026-09-08 inspected version allocation and mutation paths; adding deterministic overlap test.
Reproduced duplicate version IntegrityError in `.artifacts/knowledge-concurrency/before.log`.
The test holds first provider work, detects the second PostgreSQL backend blocked by another
transaction through pg_blocking_pids, then releases the first. Both requests now succeed with
versions 2 and 3, distinct contents and the newer title preserved despite a stale ORM instance.
Reindex/move/delete use a scoped NO KEY UPDATE read with populate_existing before mutation;
ordinary reads remain unlocked. Ruff and 46 affected tests pass in 27.90s
(`backend-corrected.log`); initial lint failure is retained in `backend.log`.
Four browser checks pass in 29.3s after API rebuild with mocks. Runtime has 543 HTTP outcomes
and zero server/error outcomes. Documentation, source-size and whitespace checks pass.
## Decisions
Keep one same-document transaction owner; ordinary reads do not acquire mutation locks.
The lock spans indexing provider I/O and releases on commit/rollback. Whole-operation deadlines,
bounded production lock waits and crash recovery remain separate requirements; no throughput
or durable-worker claim follows from this controlled overlap test.
## Findings
Current version uniqueness constraint detects collision but does not make both requests succeed.
## Final Result
Completed 2026-09-08 after reproducing the collision and verifying all scoped acceptance criteria.
Audit rollback, independently durable usage, permissions and browser integration remain green.
No unresolved P0/P1 within this repair; production deadlines and recovery remain open.
