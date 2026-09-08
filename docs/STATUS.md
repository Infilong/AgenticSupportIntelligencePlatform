# Current status

Goal: **M1–M6 authorized and active**. Current milestone: M2 real retrieval.
Branch: `codex/fresh-start`. Goal starting revision: `2c292d08b5ff9d577276c8513fc53582a1ba93d4`.
[M2 execution plan](plans/active/m2-real-retrieval.md) owns current slices and next steps;
[M1 history](plans/active/m1-foundation.md) retains foundation decisions and evidence.
Normal verified commits/pushes to this branch are authorized. No merge/deploy/paid API authority.

## Current work

Harness pushed at `a8308bf`; all 13 local regression tests and CI run `34233220196` passed
on Windows and Ubuntu. The isolated API/database now starts and migrates with pgvector enabled.
Two backend tests and lint passed. Real database outage/recovery and request log correlation
passed; source-linked runtime evidence lives in `.artifacts/m1/runtime-<timestamp>/`.
Foundation pushed as `2dd4048`; backend/preparation CI run `34234381342` passed.
Session/workspace APIs and PostgreSQL security tests are implemented; independent review
fixes are applied; 14 real PostgreSQL integration tests pass. Auth was pushed as `7d5e63d`;
CI run `34236314227` passed. Browser login/workspace/member UI and synthetic provisioning now
work with the real API/database. Five application browser journeys, two component tests,
TypeScript/build, two backend tests and 14 PostgreSQL tests pass. Chrome desktop/mobile
inspection and console check completed. UI slice final review/push is in progress.
UI pushed as `690f9dd`; CI `34239190845` passed all jobs, including the actual browser suite.
Worker foundation now exists; 23 PostgreSQL integration tests pass, including lease takeover,
concurrent claims/enqueue, rollback, cancellation and mid-handler revocation. The separate worker
processed a diagnostic in one attempt and all four containers are healthy. Worker slice review/push
is in progress. Real document ingestion/retrieval is M2; release gates remain incomplete.
Worker pushed as `5749308`; CI `34240525106` passed. M2 CPU embedding preparation is active:
actual EN/JA/ZH vectors were produced with the pinned model; warm query smoke latency was 47 ms.
Six backend unit tests and 23 PostgreSQL tests pass with the new dependency lock. Docker model
preparation now passed in the app volume (warm query 15.24 ms). Document ingestion and real
retrieval acceptance remain to complete; embedding smoke success is not a RAG quality result.
Continue through the full goal within authority; no milestone-by-milestone approval is needed.
Embedding slice pushed as `b8d04bf`; CI `34242469472` passed. Knowledge ingestion now has
11 passing unit tests and 30 passing PostgreSQL integration tests. Actual API→worker→CPU-model
ingestion stored vectors and model-call accounting and preserved the original file. Bounded
splitting refinement is under final runtime recheck. Retrieval API, knowledge UI, long-corpus
evaluation and generation workflow remain incomplete; this is not a completed RAG claim.
Ingestion pushed `59fc6c9`, CI `34245863644` passed. Real retrieval API smoke now passed,
including exact source-span verification; 35 PostgreSQL integration tests pass. Retrieval
backend slice is being checkpointed before knowledge UI and long-corpus evaluation.
Retrieval pushed `f04b86f`; CI `34247160191` passed. Knowledge UI is implemented and actual
upload/search/preview/withdrawal/restore plus mobile viewer journeys passed (2/2); existing
browser regression suite passed (5/5). UI review/checkpoint is active; long corpus remains next.
Knowledge UI pushed `c9053a8`; CI `34248740061` passed. The substantial 38.2-page-equivalent
corpus and 30-case multilingual evaluation are prepared and reviewed. Actual corpus retrieval
measurement is next; factual coverage, isolation and latency must pass independently of setup.

## Verified baseline and remaining gaps

- M0 checkpoint: `d3c8e4b1317507f8f0fd5e47d386cdfcb7d1e41c`; 10 preparation tests and one
  synthetic Chromium environment probe passed at that source snapshot. This was not app QA.
- The previous implementation is archived and must remain untouched. Runtime observations
  from M0 require reinspection before operations; no existing process is assumed live.
- Fifteen synthetic EN/JA/ZH cases exist. Full corpus, quality thresholds, live retrieval,
  actual UI/API/worker flows, restoration and release gates remain incomplete.
- [Preparation review](PREPARATION_REVIEW.md) records earlier findings; this slice addresses
  automated guide coverage and initial CI. Runtime and architecture enforcement remain open.
- Evidence is timestamped under `.artifacts/m0/` for preparation checks; summaries are mutable
  and whole-repository changes invalidate earlier source fingerprints.

## Access and failures

User currently has no API. Codex cannot act as the app's runtime API. No paid calls authorized;
use explicit deterministic test providers while implementing real integration interfaces.
User requests a Codex-assisted development handoff: app requests can be answered by this session
and imported through the provider contract, with accurate provenance and separate verification.
Generation API quality remains NOT_VERIFIED and cannot be passed from mocks or handoffs.
Retrieval must be real: local multilingual embeddings, actual vector indexing and document-derived
results will be implemented in M2. Local embedding quality must be measured independently.
M0 failures and repairs (Windows file handles, sandbox network access, UTF-8 capture) remain
recorded in the preparation checkpoint/runbook; preserve failed evidence.
Auth integration initially failed due to overridden PostgreSQL search_path connection options;
the engine now preserves them and migrations commit explicitly. Failed reports remain in artifacts.
