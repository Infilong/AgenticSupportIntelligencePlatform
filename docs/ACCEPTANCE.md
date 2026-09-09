# Acceptance matrix

M0 preparation gates are separate from product/release gates. PASS requires direct current
evidence. NOT_IMPLEMENTED and NOT_VERIFIED are not equivalent to PASS. No paid API calls are
authorized at present; external generation quality remains LIVE_NOT_VERIFIED. Real local
embedding/retrieval quality has separate evidence and does not require an external API.

## Preparation gates

| ID | Pass condition | Verification |
| --- | --- | --- |
| PREP-ISOLATION | Fresh branch recorded; old data/services preserved; new namespace/ports defined | Git baseline and doctor |
| PREP-ENV | Required tools, Docker daemon and package registries accessible | `manage.py doctor` |
| PREP-BROWSER | Fresh project-local Chromium renders EN/JA/ZH, accepts keyboard input, captures trace | `manage.py verify-browser` |
| PREP-FIXTURES | Synthetic versioned sources resolve; cases cover three languages and cross-language evidence | `manage.py verify-prep` |
| PREP-CONTRACT | Scope, topology, roles, gates, authority and next slice are explicit | Plan/docs review and local checkpoint |

## Product gates

| ID | Pass/fail contract | Release verification method (coverage below) |
| --- | --- | --- |
| BOOT | Fresh isolated install migrates and becomes healthy with built assets | Fresh Compose/application E2E |
| AUTH | Login/logout/expiry, role denial and last-admin protection hold | API + browser auth tests |
| TENANT | A cannot read/write/retrieve B's data, including queued jobs and artifacts | PostgreSQL security matrix |
| KNOW | Upload, indexing, replacement activation and withdrawal retain exact originals/history | Ingestion/version integration and browser |
| RAG | Expected evidence retrieved; required facts supported by valid authorized citations | Fixed retrieval/live answer cases |
| LANG | EN/JA/ZH output language and cross-language evidence are correct | Per-language fixed cases |
| ROUTE | Clarification, missing/conflicting evidence, review and technical failure stay distinct | Graph branch tests and browser journeys |
| REVIEW | Approve/edit/reject survives restart; competing decisions cannot double-finalize | PostgreSQL concurrency and browser |
| JOB | Crash/lease expiry/replay/cancellation preserve correct state and uncertainty | Worker fault injection |
| DATA | Imported/labelled messages can actually start processing | Real import→select→run journey |
| TRACE | UI evidence, model, durations/tokens/cost agree with stored records | Ledger/trace integration and UI inspection |
| EVAL | direct_llm/vector_rag/hybrid_rag/system_v1 execute distinct comparable pipelines | Baseline routing and live corpus report |
| UX | Main journeys and failure states work with keyboard, 360/768/1440px and 200% zoom | Actual app Playwright + visual inspection |
| RESTORE | Backup fingerprints match restored data; restored app handles a new request | Isolated restoration drill |

Every implemented behavior needs happy-path, failure and permission-denial coverage where
applicable. Product checks use real PostgreSQL and application paths; deterministic provider
fakes cannot prove live semantic quality. Zero unauthorized disclosure is a mandatory security
criterion, not an average score. Browser screenshots alone do not prove backend behavior.

### Current partial evidence

The table above is the release contract, not a claim that all gates passed. Current evidence
and exact artifact paths are recorded in [status](STATUS.md) and the
[M2 execution record](plans/active/m2-real-retrieval.md).

- AUTH: implemented with API/database and browser tests. Full release-session/security matrix
  remains to be checked with the completed application.
- TENANT/JOB: foundation, knowledge and support message/graph paths have real PostgreSQL
  coverage, including concurrent claims/submissions, lease takeover, revocation, cancellation
  and source withdrawal/replacement. Human-review concurrency, revocation, publication fencing
  and graph recovery have focused PostgreSQL evidence. Worker restart at review wait succeeds;
  the complete process-kill/recovery matrix remains pending.
- KNOW: real TXT/Markdown upload, indexing, exact originals, versions, replacement failure,
  withdrawal/restore and desktop/mobile knowledge journeys pass.
- RAG: frozen local retrieval gate passes (26/26 evidence cases, 27/27 source groups,
  zero forbidden leaks, 2.5-second warm p95). Development draft/citation provenance is tested;
  semantic claim support remains unverified, so the full RAG gate is not complete.
- LANG: cross-language retrieval is measured; EN/JA/ZH Codex-assisted response smokes pass.
  These manually authored development drafts do not establish a generation-language quality gate.
- TRACE: the workbench exposes graph steps and local embedding/reranking records, including
  identity, duration, tokens and external charge. Retrieval ownership/reconciliation has focused
  process-kill, session-loss and late-write tests within the passing 100-case PostgreSQL suite.
  Complete generation accounting and the broader crash matrix remain incomplete.
- REVIEW/ROUTE: operator/admin clarification preserves the unapproved draft and immutable
  question; customer replies start fresh linked retrieval. The 110-case PostgreSQL regression,
  nine browser journeys and four publication-state component cases pass. This proves the
  clarification software flow, not automatic semantic routing or the full release gates.
- UX: connected draft/source/cancellation and approve/edit/reject journeys pass, including 360/768/1440px, keyboard
  source focus and doubled content size. Browser-native zoom and full release journeys remain open.
- Inbox views: latest-attempt filtering, matching counts, workspace denial and pagination pass
  within the 113-case PostgreSQL regression. The real filtered inbox journey passes at all three
  widths; a shrinking-page component regression and mobile navigation overflow repair are verified.
  The later capacity check verifies 50,000 primary stored-state messages, 100 foreign messages,
  exact latest-attempt ordering/counts, concurrent admission and a real browser on an isolated
  API/database. Full PostgreSQL regression has 116 passing cases. Five warm samples per query
  stayed below the unchanged 1,000ms local target after measured repairs; this is not production
  throughput, a stable latency percentile or proof of 50k AI executions. These views do not
  complete the imported/labelled-message DATA gate.
- Linked attempts: PostgreSQL tests cover history, fresh retrieval, atomic competing submissions,
  creator revocation, scoped lineage and limits. The browser clarification/cancel/retry/history
  journey and repaired viewer fixture pass. This advances DATA/ROUTE/JOB/UX
  without completing imports, semantic routing or the complete recovery matrix.
- ROUTE/REVIEW/DATA/EVAL/RESTORE and full BOOT/UX release coverage remain incomplete.

## Evaluation expansion gate before M2 tuning

M0 started with 15 seed cases. M2 expanded and froze 30 cases (10 per language) and a
38.2-page-equivalent synthetic corpus before measurement; see
[the corpus contract](../evals/corpus/v1/README.md) and [freeze](../evals/corpus/v1/freeze.json).
It covers renewals, day boundaries, active conflicts, withdrawal, document instructions and
cross-language retrieval. Four cases concern generation/routing outcomes and are not counted
as retrieval evidence cases.

Before measuring improvements, record source-equivalence mapping, retrieval k, expected
facts, scoring rubrics, per-language denominators, numeric pass thresholds and latency budgets.
Frozen retrieval thresholds are at least 90% overall and 80% per language for both evidence-case
success@5 and required-section-group recall@5, zero forbidden leaks, and warm p95 <= 3 seconds.
The fixed denominators are 26 cases/27 groups. These thresholds were set before measurement;
selecting easier thresholds after seeing failures is not allowed. Generation thresholds and
four-pipeline comparisons remain separate pending work; [RAG design](RAG.md) details the audit gaps.
If an approved criterion must change, record the change and obtain product approval.
Compare identical case sets and compatible generation settings across all four pipelines.

Release output includes revision/source fingerprint, dependency/config/corpus hashes, commands,
exit codes, passed/failed/skipped/blocked counts, screenshots/traces and live spend estimate.
Final status distinguishes VERIFIED_LOCAL_OFFLINE, VERIFIED_LOCAL_LIVE, PARTIALLY_VERIFIED,
BLOCKED and AWAITING_HUMAN_RELEASE_REVIEW; no general production-ready claim.
