# Agent-first documentation consolidation

## Goal
Implement the user's requested concise instruction map, focused contracts and execution history.
## Context
Existing AGENTS.md, documentation router, product/coding/security/observability/planning docs,
and current test evidence were inspected. Official Codex guidance is linked in CORE_BELIEFS.md.
## Requirements
Preserve project invariants, use progressive disclosure, avoid duplicate manuals, expose honest
quality gaps and retain existing links/history. No application changes in this documentation pass.
## Non-goals
Production certification, mass migration of historical tickets, model changes or deployment.
## Acceptance Criteria
Requested control files exist; AGENTS.md stays concise; local links resolve; overlapping workflow
and architecture manuals are consolidated; quality claims match evidence; plans have a lifecycle.
## Plan
1. Inspect existing guidance and runtime evidence.
2. Consolidate instruction/architecture/workflow ownership and add missing contracts.
3. Establish active/completed plan routing; preserve legacy link entry points.
4. Validate changed docs, links, plan sections and source-size policy; review the complete diff.
## Verification
Check local Markdown targets and required plan sections; count AGENTS.md lines; run diff whitespace
check. Reuse the completed local runtime run for dated claims; docs edits do not need app retests.
## Risks
Breaking old links, duplicating policy and confusing intended behavior with implemented behavior.
## Progress
2026-09-08 recovery documentation audit: re-read the attached documentation-only request,
existing control structure, product/security/observability/coding guides and official OpenAI
sources linked in CORE_BELIEFS.md. Retained the 56-line AGENTS.md, focused guides and existing
CI enforcement. Corrected the quality table's stale all-green wording against the saved 28/29
browser log, removed repeated test chronology, and distinguished historical compiled-image
acceptance from later changes. Updated code-map ownership for embedding orphan recovery and
made the tooling guide route current status to the scorecard. Existing implementation and
failed evidence were preserved. No application, test, dependency or runtime changes were made.
Validation: documentation gate, all 26 tooling tests, source-size gate (179 application files)
and whitespace check passed. Tooling tests simulate runtime success/failure; no application
suite or live deployment was rerun. The broader production and navigation plans remain active.

2026-09-08 built-web evidence audit: inspected the attached documentation-only request and
retained the existing control structure, subsystem guides and 56-line AGENTS.md. Rechecked
official AGENTS.md guidance, CI wiring, current trace readers and the saved built-web logs
(26 browser passes, one failure). Corrected the quality table's stale passing/latest claims,
removed duplicated regression chronology, and documented timestamp-ordering limitations in
the owning observability guide. Graph sequencing remains an active implementation plan.
Validation: `python scripts/check_docs.py`, `python -m unittest discover -s scripts/tests -q`
(26 tests), `python scripts/check_source_sizes.py` (171 application files), and
`git diff --check` passed. Tooling tests simulate failure paths; they do not rerun Docker or
browser acceptance. Only the quality score, observability guide and this history changed.
No application code, dependencies, runtime processes or existing failed artifacts changed.

2026-09-08 server-logging documentation audit: inspected the latest attachment, existing control
structure, product/coding/security/observability contracts, source owners and saved test logs.
Retained the 56-line AGENTS.md and existing executable gates; checked the official sources
linked in CORE_BELIEFS.md. Updated six existing documents: observability and code-map ownership,
testing evidence, quality score, the active production handoff and this execution history.
Removed repeated scoped test history from the scorecard and corrected the current source count.
The active plan now explicitly respects this documentation-only request before selecting work.
Saved server evidence passes 22 backend tests; those tests were inspected, not rerun here.
Current audit verification passes the documentation gate, all 22 tooling tests, the source-size
gate (168 application files) and whitespace review. No application code, tests, dependencies,
runtime configuration or runtime processes changed during this pass. Full release remains open.

2026-09-08 current request audit: retained the existing requested structure and 56-line AGENTS.md.
Rechecked official OpenAI source pages and CI wiring; existing executable gates cover the
document map, plan sections, instruction length, source sizes and tooling regressions.
Updated six existing documents to record saved error-reference evidence, correct stale
language-acceptance wording and file counts, and identify current logging/error-response owners.
The active feature plan now distinguishes passing saved checks from its outstanding final
review. No application code, tests, dependencies or runtime were changed for this audit.
Validation: documentation gate, 19 tooling tests, source-size gate (164 files) and whitespace
check pass. Application evidence was inspected, not rerun. Broader release work remains active.

2026-09-08 current-worktree evidence audit: re-read the attached documentation-only request,
control files, product/coding/security/observability guides and the official OpenAI sources.
Retained the requested structure and 56-line AGENTS.md without duplicate instructions or checks.
Updated five existing documents: quality score, code map, testing evidence, explicit-language
active plan and this history. Recorded the new module owners, corrected stale size counts,
and separated the saved 83-test backend pass from the unresolved nine-failure browser run.
The active plan now contains a concrete continuation handoff; its feature is not marked done.
Documentation gate, all 19 tooling tests, source-size gate (160 application files) and
`git diff --check` pass. Application code, tests, runtime and dependencies were not changed
or rerun in this audit. Existing uncommitted work and failed artifacts were preserved.

2026-09-08 evidence/structure audit: retained the existing requested control files and 56-line
AGENTS.md after inspecting the attached scope, architecture, product, coding, security,
observability, planning and local guides. Rechecked official OpenAI source pages linked in
CORE_BELIEFS.md. Removed duplicated intermediate test chronology from QUALITY_SCORE.md while
preserving it in testing.md; changed the migration claim to describe the saved verification,
not an uninspected live stack. Updated the code-map refactoring order to reuse the extracted
HTTP transport and preserve root session rejection. Confirmed CI already runs documentation,
source-size and tooling gates; no additional executable check was necessary.
Validation: documentation gate, all 17 tooling tests, source-size gate (156 application files),
and whitespace check passed. Re-read saved 36-test focused, 427-test backend and 24-test browser
logs for evidence attribution; application suites were not rerun. Only these two owning guides
and this history record changed in this audit. Application changes remain outside this scope.

2026-09-08 documentation maintenance pass: checked the attached request against the existing
control structure and current CI gate. Removed transient session-status wording from the Codex
workflow entry, marked product-spec prose as requirements rather than verified capabilities,
and added documentation maintenance/validation routing. Rechecked the official source links in
CORE_BELIEFS.md. No application or tooling code changed; existing worktree edits were preserved.
Validation passed: documentation gate, all 17 tooling tests, source-size gate (153 application
files), and `git diff --check`. Root AGENTS.md remains 56 lines. Application suites were not
rerun for this documentation-only pass; no new runtime or production-readiness claim is made.

2026-09-08 follow-up audit: re-read the attached documentation-only request, instruction/router,
architecture, product, coding, security, observability and planning documents. Rechecked official
OpenAI AGENTS guidance and the two source articles linked in CORE_BELIEFS.md. The requested
structure and CI checks already exist; no duplicate guides or application edits were needed.
Corrected stale evaluation descriptions in the code map and separated current saved test
evidence from the older full-runner result in QUALITY_SCORE.md. Removed duplicated repair
chronology from that scorecard. PLANS.md now explicitly requires current-request scope checks
on resume; the broader active production plan reflects this documentation-only pass.
Validation: `python scripts/check_docs.py`, all 17 tests from
`python -m unittest discover -s scripts/tests -q`, `python scripts/check_source_sizes.py`
(146 application files), and `git diff --check` pass. AGENTS.md remains 56 lines. Inspected
saved backend/browser logs; did not rerun application suites or claim production readiness.

2026-09-07 subsystem-guide follow-up: checked the attached scope against the existing structure
and current implementation. Corrected stale backend, migration and retrieval guidance without
changing application code. Extended the existing documentation gate to the seven local guides;
added a regression that proves missing guides and broken subsystem links fail validation.
All 17 tooling tests, the documentation gate, source-size gate (138 application files), and
`git diff --check` pass. CI and the Windows runner already invoke these checks. Root AGENTS.md
remains 56 lines. No backend/browser rerun was needed for documentation and tooling changes.

2026-09-07 follow-up audit: re-read the user's attached documentation-only scope and the
existing control/module guides. Retained the requested structure without duplicate manuals.
Corrected stale budget/concurrency descriptions and recorded the saved multilingual policy
failure in the evidence owner and scorecard. Clarified that the active release plan cannot
override a narrower user request. Application code and existing tests were left untouched.
Follow-up validation passed: `python scripts/check_docs.py`, all 16 tests from
`python -m unittest discover -s scripts/tests -q`, `python scripts/check_source_sizes.py`
(135 application files), and `git diff --check`. AGENTS.md remains 56 lines. The existing
documentation/size gates already run in CI and the Windows runner; no new checker was needed.

2026-09-07: inspected existing docs, consolidated owners and added the requested control structure.
Validated the documentation gate and all 16 tooling tests; checked source sizes and whitespace.
The cross-document review found zero broken local targets in 34 changed/new Markdown files.
Moved this scoped plan to completed after reviewing acceptance. Production work remains active.
## Decisions
Keep compatibility pages for architecture/workflow/production-loop links. Preserve historical
tickets; root architecture describes current boundaries, while design docs retain requirements.
## Findings
Old workflow duplicated plan/review instructions. Architecture implied workers/resume existed;
current code and audit show these are gaps. Full local runner passed 14 checks before this pass.
## Final Result
Completed 2026-09-07. AGENTS is a concise map; root architecture, beliefs, reliability, quality
score and plan lifecycle have distinct owners. Legacy entry links and ticket history remain.
The doc gate enforces maintained links, plan sections and instruction size. No application code
changed in this documentation pass; prior implementation/CI work remains uncommitted.
