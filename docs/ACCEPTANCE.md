# Acceptance matrix

M0 preparation gates are separate from product/release gates. PASS requires direct current
evidence. NOT_IMPLEMENTED and NOT_VERIFIED are not equivalent to PASS. No live API calls are
authorized at present; live quality remains LIVE_NOT_VERIFIED.

## Preparation gates

| ID | Pass condition | Verification |
| --- | --- | --- |
| PREP-ISOLATION | Fresh branch recorded; old data/services preserved; new namespace/ports defined | Git baseline and doctor |
| PREP-ENV | Required tools, Docker daemon and package registries accessible | `manage.py doctor` |
| PREP-BROWSER | Fresh project-local Chromium renders EN/JA/ZH, accepts keyboard input, captures trace | `manage.py verify-browser` |
| PREP-FIXTURES | Synthetic versioned sources resolve; cases cover three languages and cross-language evidence | `manage.py verify-prep` |
| PREP-CONTRACT | Scope, topology, roles, gates, authority and next slice are explicit | Plan/docs review and local checkpoint |

## Product gates — all NOT_IMPLEMENTED at M0

| ID | Pass/fail contract | Planned check, not yet executable |
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
| EVAL | direct_llm/vector_rag/system_v1 execute distinct comparable pipelines | Baseline routing and live corpus report |
| UX | Main journeys and failure states work with keyboard, 360/768/1440px and 200% zoom | Actual app Playwright + visual inspection |
| RESTORE | Backup fingerprints match restored data; restored app handles a new request | Isolated restoration drill |

Every implemented behavior needs happy-path, failure and permission-denial coverage where
applicable. Product checks use real PostgreSQL and application paths; deterministic provider
fakes cannot prove live semantic quality. Zero unauthorized disclosure is a mandatory security
criterion, not an average score. Browser screenshots alone do not prove backend behavior.

## Evaluation expansion gate before M2 tuning

M0 has 15 seed cases and five source files, including one inactive version. It does not meet
the release requirement of at least ten cases per language or a 30–50-page-equivalent corpus.
Expand coverage before tuning: paraphrases, renewals, day boundaries, missing information,
active conflicts, withdrawal, prompt injection, and cross-language retrieval.

Before measuring improvements, record source-equivalence mapping, retrieval k, expected
facts, scoring rubrics, per-language denominators, numeric pass thresholds and latency budgets.
Thresholds are currently NOT_SET; selecting easier thresholds after seeing failures is not allowed.
If an approved criterion must change, record the change and obtain product approval.
Compare identical case sets and compatible generation settings across all three pipelines.

Release output includes revision/source fingerprint, dependency/config/corpus hashes, commands,
exit codes, passed/failed/skipped/blocked counts, screenshots/traces and live spend estimate.
Final status distinguishes VERIFIED_LOCAL_OFFLINE, VERIFIED_LOCAL_LIVE, PARTIALLY_VERIFIED,
BLOCKED and AWAITING_HUMAN_RELEASE_REVIEW; no general production-ready claim.
