# Explicit support language
## Goal
Let users select EN/JA/ZH for ambiguous support input and preserve evaluation case language.
## Context
At the start of this ticket, kanji-only Japanese became Chinese; the run API had no language
field and system-v1 ignored declared evaluation language. Legacy services/UI must shrink
when gaining this behavior. The current working tree contains an unaccepted implementation.
## Requirements
Optional validated language, auto default, traced selection source, retrieval/model propagation,
UI Auto/English/Japanese/Chinese choice, same permissions and request limits.
## Non-goals
Probabilistic language identification, translation, new providers, billing or schema migration.
## Acceptance Criteria
Kanji-only input explicitly selected as Japanese retrieves Japanese evidence and produces a
Japanese run; trace and ledger language match. Omitted language keeps auto behavior. Invalid
language rejected before run creation. Evaluation uses declared language. UI selection is submitted.
## Plan
1. Extract run-context preparation; add schema/state/graph selection and evaluation propagation.
2. Extract run-console rendering with a language selector; send form language with the message.
3. Add backend and browser regressions; lint/build, review traces, document limits.
## Verification
Focused provider/graph/evaluation/authorization tests and live browser workflow. Use mock providers.
## Risks
Auto detection remains heuristic. New choice must not bypass response-language guardrails or
permissions. Preserve legacy API callers. Keep a single implementation owner across coupled work.
## Progress
2026-09-08 inspected request/service/graph/evaluation/UI boundaries; implementation authorized
by the ongoing full-platform goal. No external calls or migration required.

2026-09-08 documentation-only handoff: optional request language, graph selection provenance,
evaluation propagation, run-context helper and run-console component are present. Saved
corrected backend checks pass 83 tests; frontend build passes. Latest saved browser run has
nine failures and 16 passes. Detailed results belong in [testing](../../testing.md#explicit-support-language-in-progress).
The current attached request excludes application edits, so this feature remains active.
On an implementation continuation, inspect the worktree and runtime before resuming:
1. Verify the corrected evaluation call is in the API image; rebuild with mock providers.
2. Repair the new test's exact-host response matcher after checking the configured client URL.
3. Diagnose the notification failure from its trace before changing timing or assertions.
4. Rerun browser acceptance and relevant regressions; update evidence and subsystem contracts.
## Decisions
2026-09-08 implementation continuation: rebuilt the corrected API with mock providers and
changed the new browser matcher to use the workspace endpoint pathname. All 25 browser checks
pass, including explicit Japanese/Auto payloads, trace provenance, multilingual evaluation
and permissions. Fresh frontend build passes; corrected runtime has 2,291 HTTP outcomes and
zero server/error outcomes. Full backend/PG regression is running; do not infer its outcome.

Store requested language and selection source in graph step state; selected language already
has a GraphRun field. Split cohesive responsibilities instead of growing legacy files.
## Findings
The first edit accidentally passed language to `_run_case`, producing evaluation failures;
the current source removes that argument and the corrected backend suite passes. The prior
browser image was built before this correction. The new browser test compares the full
agent-creation response URL to its API fixture base; hostname differences can prevent a match.
The notification failure still needs trace-based diagnosis. Preserve all failed artifacts.
## Final Result
Completed 2026-09-08: optional EN/JA/ZH selection, automatic compatibility, evaluation case
propagation, traced provenance and UI selection pass acceptance. Full backend lint and
474 tests (PostgreSQL enabled), 25 browser checks, frontend build/types and 19 tooling tests
pass. Documentation/source-size/whitespace gates pass. No migration or paid-provider call.
Earlier failures remain recorded. Automatic detection and real-provider language quality
retain their limits; the earlier slow refresh needs separate performance investigation.
