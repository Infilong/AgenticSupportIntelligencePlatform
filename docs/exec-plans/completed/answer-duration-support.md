# Cited duration support
## Goal
Route drafts with numeric durations absent from their cited evidence to human review.
## Context
Unsupported-answer checks currently accept any retrieved chunk. Exact citations do not establish
factual support, so a cited seven-day policy can accompany an invented 700-day answer.
## Requirements
Compare numeric durations against the nonempty packed chunks actually cited. Handle EN/JA/ZH
duration units and normalized full-width digits. Do not use uncited chunks or citation titles as
support. Preserve permissions, provider ledger, graph traces and configurable guardrail actions.
## Non-goals
Full semantic entailment, currency/date parsing, word-number conversion, automatic unit conversion,
model-judge calls, or replacing human judgment with a heuristic.
## Acceptance Criteria
EN/JA/ZH provider drafts with invented durations cannot automatically finalize under default
policies, retain proposed answers/usage/traces and reach human review. Matching duration excerpts
remain usable. Tests distinguish supported, absent, uncited and metadata-only quantities.
## Plan
1. Reproduce the cited-but-invented deadline through real graph API execution with mock providers.
2. Put cited-text extraction in answer_citations; duration normalization/comparison in a focused
   answer_duration_support helper; reuse it in graph routing and final guardrail publication.
3. Run relevant API/guardrail/review tests, rebuild and verify browser workflows; update owning docs.
## Verification
Keep reproduction and corrected runs under `.artifacts/answer-duration-*`. No paid providers.
Run Ruff, focused tests, source-size/docs checks, relevant browser acceptance and inspect logs.
## Risks
Matching quantities do not prove entailment: relation changes, negation and other facts remain
unverified. Correct paraphrases or conversions may conservatively require review. Do not advertise
this check as a complete factual-support grader. Human review retains authority over publication.
## Progress
2026-09-08: inspected current presence-only unsupported guard and packed-citation validator.
The reproduction failed seven cases, including all three provider/API languages, and passed
two supported cases (`.artifacts/answer-duration-before.log`). Added shared cited-text extraction
and deterministic duration comparison to routing and final guardrails. Ruff and 108 focused
tests passed; one PostgreSQL-only case was skipped and remains for the full pipeline.
Final full pipeline `.artifacts/20260907T234548644Z/` passed all 17 gates: 632 backend tests
with PostgreSQL enabled, 26 tooling tests, lint/build/types, source/docs checks and both full
27-test browser suites. Compiled-image evidence:
`.artifacts/built-web-9d73604ad4174767bccc760623c9ada5/` (39.5s browser run).
Runtime review: 2,470 HTTP outcomes in the API run window and 1,787 in the separate image
window, neither with server/error outcomes. API startup and production-mode image checks passed.
All verification processes completed; no browser assertion, concurrency or timeout was weakened.
## Decisions
Use deterministic checks before adding model cost. Preserve the broader factual-support gap.
## Findings
Default policies previously finalized 700-day answers citing seven-day evidence. Quantity
comparison excludes uncited chunks and citation metadata, normalizes digits and supported unit
aliases, and retains conservative review for unit conversions or business/calendar-day changes.
## Final Result
Completed for detecting numeric durations absent from cited evidence, preserving human-review
and usage/trace behavior, with full local regression. No semantic-entailment or real-provider
quality claim. Remaining factual-support limitations stay in the broader production plan.
