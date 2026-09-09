# Five-session local release profile

## Execution brief

User outcome: verify the release contract's small internal-team profile and actual admin/operator
inspection/intervention. Advance BOOT/TRACE/JOB/UX; do not tune retrieval or claim generation quality.
Normal verification slice, root implementation owner. Read root/frontend/backend/support/infra/
scripts/docs guides. Preserve existing development/archive services and all databases/volumes.

Refresh the existing isolated built release to the verified application snapshot. Use its seeded
synthetic administrator plus five independent browser sessions for the seeded operator. Upload a
real long synthetic company-policy document through the app, then submit five language-labelled
requests concurrently while a second document indexes. Real CPU embeddings, pgvector retrieval,
reranking, worker and LangGraph stay enabled. No external generation calls or spending.
Inspect each waiting run's stored trace/model metadata and cancel through the operator UI.
This tests concurrent sessions and the pre-generation workflow, not five simultaneous inferences,
distinct human identities, automatic answer quality, throughput guarantees or a production SLO.

Record fixture bytes, active documents/chunks, actual submission/ingestion/handoff/cancellation
latencies, request/run/job/trace identifiers, and database admission-to-first-node timing. The last
metric includes queue wait plus work before the first recorded node; do not label it pure queue
wait or invent missing timestamps. Preserve failures and unknown/clock-anomaly measurements.
Keep queries and records bounded and workspace-scoped. Reuse current product APIs/UI; add only
the verification harness and a small read-only measurement command if needed. No product refactor.

Verification: TypeScript/build, actual built-app browser journey with five active contexts and
background ingestion, model/trace/DB agreement, permission controls and terminal cancellation.
Inspect screenshots and scoped logs. Independently review harness/measurement claims, update
owning docs, preparation/freshness checks and commit/push. Stop at the existing unattended boundary.

## Results

Completed bounded verification from historical-evaluation checkpoint855d1e1. No product runtime
behavior, schema, retrieval strategy or API contract changed. Added a five-session browser journey
and read-only PostgreSQL measurement CLI with five focused integration cases. RAG tuning remains
deferred. Chrome login is still pending; these are isolated synthetic-account browser contexts.

Final built release refresh: `.artifacts/m0/release-up-20260909T125652601319Z`, healthy API/worker/
PostgreSQL. Built assets remain index-DskUr9Hh.css and index-vT9loU-E.js. Backend additions are
measurement-only. Final browser: `.artifacts/m6/small-team-final-20260909`, one pass in42.9 seconds
(45.1-second runner); profile.json records a25.24-second concurrent measurement window after
initial ingestion/session setup. All five runs are cancelled, each has two succeeded local CPU
model records and a completed retrieval trace with final ranking; no page errors. Three graph
step records per run are retained. Operators cannot see development response controls.

The two policy fixtures contain28,594 and33,621 bytes (62,215 total). Their version IDs and hashes
are in profile.json and database-profile.json. Collection-time active corpus: five documents,
124,615 bytes,128 chunks; earlier synthetic records are preserved. This is not a clean-corpus
benchmark, and counts were collected after the workload rather than inferred for every retrieval.

| Measurement | Final local sample |
| --- | --- |
| Browser request admission, five runs | 204–450 ms |
| Browser observed handoff, from coordinated start | 9.56–18.88 s |
| Browser cancellation | 147–376 ms |
| DB admission to first recorded node | 2.39–14.07 s |
| DB admission to development handoff | 7.86–16.66 s |
| DB initial / background admission to indexed | 15.15 / 22.58 s |

The stored background interval12:58:58.182925–12:59:20.761961 UTC intersects the five-run
admission-to-handoff interval12:58:57.940159–12:59:14.620976 UTC. The CLI reports overlap=true.
These intervals include queued work; first-node timing also includes pre-node work. API/worker
logs in the same artifact directory were inspected: all seven jobs succeeded on attempt1,
no request4xx/5xx or job errors in the bounded window. Model-loading/deprecated cache_dir warnings
remain visible; they did not prevent real model execution. Chinese final screenshot was inspected;
the earlier passing run's English/Chinese screenshots were also inspected.

## Review and verification

- Five PostgreSQL tests pass in10.25s at
  `.artifacts/m0/release-profile-20260909T125150482716Z`: workspace/missing-record rejection,
  read-only enforcement, unknown/negative timing and positive/negative interval overlap.
- TypeScript/Vite build passes. Standalone strict TypeScript check of small-team.spec.ts passes;
  the normal UI tsconfig excludes e2e files. Ruff passed on the helper and focused tests.
- Earlier real browser pass retained at `.artifacts/m6/small-team-20260909` (42.3s test).
  Its database snapshot was collected later and is explicitly collection-time data.
- Independent reviewer found promise rejection/evidence-finalization races and insufficient
  overlap evidence. Repairs attach handlers immediately, settle all tracked outcomes before
  saving final failure, and add authoritative persisted-interval checks. Final upload/admission
  response and click promises settle together even when click fails. Browser rerun passes.
- An automatic approval-review timeout prevented one SQL-test launch; the instructed single
  retry launched successfully. No database test failure was hidden by that retry.
- Full155-case PostgreSQL regression and65 backend units from855d1e1 predate these additions;
  they are not rerun evidence for the new helper. Documentation review/preparation recorded below.
- Independent code review closed without remaining actionable findings. Independent semantic
  review verified saved measurements and renewed all six exact area receipts. Freshness check
  passes;46 preparation checks pass in7.620s at `.artifacts/m0/prep-20260909T130840658739Z`.
  This completion note was added afterward; source behavior and reviewed owning docs are unchanged.

## Limits and next step

No automatic generation, semantic answer quality, simultaneous model inference, approval throughput,
held-out evaluation or production SLO is established. This uses five sessions of one operator,
not five distinct users. Corpus/model caches are local and small;50k retrieval tuning stays parked.
Failed browser journeys may leave admitted records/jobs for diagnosis. The CLI is trusted local
database tooling, not a newly permissioned application endpoint. Full goal remains incomplete.
Checkpoint this verification, then continue a bounded release gap within the current authorization.
