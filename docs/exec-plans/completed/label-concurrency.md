# Concurrent human labels
## Goal
Make concurrent human label creation/update reliable without losing requested values.
## Context
Human label upsert queries before insertion; uniqueness prevents duplicates but can fail a
request. Cached labels can also prevent restoring a value changed by another session.
## Requirements
Serialize edits on the scoped conversation, refresh labels, preserve imported labels and actors.
## Non-goals
Optimistic conflict UI, label history/audit expansion, dataset deletion races, durable retries.
## Acceptance Criteria
Concurrent initial edits both succeed with one human label; stale edits persist their requested
value/actor. Existing permission and dataset tests remain green.
## Plan
1. Reproduce first-insert collision and stale-value failure on PostgreSQL.
2. Lock the conversation before label lookup; refresh label state before mutation.
3. Verify PostgreSQL, existing boundaries and browser integration.
## Verification
Controlled overlap and retained stale instances, Ruff, affected tests and browser journeys.
## Risks
Serialized last writer wins is existing API semantics, not explicit user conflict resolution.
## Progress
2026-09-08 two regressions fail on PostgreSQL (`.artifacts/label-concurrency/before.log`).
Applying a scoped lock and refreshed label query; source size remains below 300 lines.
Both reproduced failures are repaired: scoped conversation NO KEY UPDATE precedes label lookup,
and populate_existing refreshes cached labels. Ruff and 38 affected tests pass in 20.74s
(`backend.log`), including PostgreSQL and existing permission/audit/import regressions.
Four browser checks pass in 32.6s after mock API rebuild; 543 HTTP outcomes contain no server
errors. Documentation/source-size/whitespace checks pass. No provider or schema changes.
## Decisions
Lock the parent even when the label does not yet exist. Normal conversation reads remain unlocked.
## Findings
Unique label constraint alone cannot serialize first creation; ORM cache can hide a newer value.
## Final Result
Completed 2026-09-08. Concurrent first edits share one label ID and stale edits persist requested
value/actor. No unresolved P0/P1 in this scope. Conflict UI, history and deletion races remain open.
