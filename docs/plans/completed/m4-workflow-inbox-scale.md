# Admin workflow inspection and high-volume inbox

## Execution brief

The user approved resuming M1–M6 from the latest checkpoint, prioritizing an actual visible
workflow and an inbox suitable for tens of thousands of messages. Start: 2026-09-09 06:04:24 UTC;
stop unattended work by 10:04:24 UTC. Base: 00bfe7e; preserve the full release objective.
No paid API, merge, deployment, archive changes or new infrastructure. Root owns implementation;
independent agents provide bounded read-only semantic/security/performance review.

Acceptance: TRACE, UX, DATA and TENANT. This is deep work: preserve server authority and
recorded evidence while changing navigation; measure capacity before claiming it.

## Ordered slices

1. Visible workflow inspector from actual domain records: input validation → retrieval/context
   → attributed development response → human review → result. Context is part of retrieval,
   not a fabricated separately timed node. Show recorded status/attempts/errors/model calls;
   distinguish skipped, not reached, waiting and unknown. LangChain integration is not a second graph.
2. Full-width, compact paginated message table and dedicated detail views for Response, Workflow,
   Sources and History. Preserve search/filter/page on return and accessible keyboard/mobile behavior.
3. Exercise 50,000 synthetic messages with the real query path and isolated database; inspect
   latency/query plans and current 10,000-message cap. Adjust bounded API/navigation/indexes only
   with evidence. Retain server filtering, permission denial and stable ordering. Do not load
   all messages in the browser or turn a table mockup into a capacity claim.
4. Independently review, update owning docs/receipts, verify and commit/push each coherent slice.
   Then select remaining dependency-ready release work under the full goal and current window.

Verification: targeted state/interaction tests; backend PostgreSQL checks for changed query/cap
boundaries; actual Chrome and saved browser journeys at 360/768/1440px; representative 50k
pagination/search/filter timings; source-bound evidence, unchanged thresholds and no fabricated AI.
Remaining RAG reviewer P2 findings retain their separate record; do not silently declare them fixed.

## Workflow and navigation checkpoint

Implemented four recorded stages, separate publication outcome, inspectable local model calls,
terminal unfinished/paused states and chronological invocation history. Response controls stay
mounted across accessible tabs; cancellation stays above them. Full-width inbox uses persisted
URL filters/page and bounded 20/50-row requests, with direct page entry and no hidden list poll.

Evidence: TypeScript/Vite build and 23 tests passed. Nine existing workbench journeys passed in
`.artifacts/m4/workflow-inbox-ui-20260909`; its tenth/inbox case failed mobile page overflow.
Fix: allow the shell grid child to shrink so only the table scrolls. Both focused inbox/workflow
journeys then passed in `.artifacts/m4/workflow-inbox-ui-fixed-20260909` (29.0s), including
360/768/1440 screenshots inspected by root. Chrome showed the actual approved Japanese run's
four stages and embedding/reranker records. Six workflow-state cases initially were silently
excluded by the `.test.tsx`-only test glob; the glob now includes both extensions and they pass.
Independent reviewer: no P0/P1; fixed source focus and viewer compose deep-link P2s with tests.
No backend semantics/schema changed in this slice. Next: real isolated 50,000-message query
measurements and admission-limit decision, then remaining goal work within the current window.

## Capacity measurement protocol

Before tuning: 50,000 primary + 100 foreign synthetic stored-state messages, 500 newer
attempts, real migrated PostgreSQL and actual HTTP route validation via TestClient. Check
first/middle/last pages, each latest-attempt view, selective and Japanese searches, exact stable
ordering/counts, viewer reads, cross-workspace denial and 50-row response limit. No provider
jobs run in this fixture. Capture first observation plus five warm samples per case and
EXPLAIN ANALYZE/BUFFERS. Local target is warm per-case p95 <= 1,000ms, set before measurement;
CI retains deterministic correctness checks without a hardware-sensitive timing assertion.
API admission at 50k and browser capacity remain separate required checks. Do not confuse
bulk fixture insertion beyond the current 10k cap with supported message admission.

## Capacity result

Completed the planned stored-state capacity boundary. Baseline 50k first/deep warm maxima were
403/960/737ms; plans exposed repeated latest-run resolution in counting/deep pagination.
All-view message-ID paging/count reduced that work while preserving runless-row exclusion.
A repeat failed the unchanged 1,000ms budget on Failed view at 1007.1ms; scoped NOT EXISTS newer
attempts now allows filtered queries to prune candidates before latest-attempt exclusion.
Independent SQL review found no ACL/latest-state/order regression. No migration/index was needed.

Final command `verify-inbox-capacity`: six checks pass, actual isolated browser passes with
50k data, admission races admit exactly the 50,000th message and replay adds no job. Evidence:
`.artifacts/m0/inbox-capacity-20260909T065459385520Z`; five warm samples per case ranged 65.7–234.1ms
at their maxima, not stable production percentiles or AI throughput. Full PostgreSQL regression
116 passed in 291.36s at `.artifacts/m0/integration-20260909T065711706876Z`; 24 unit checks pass at
`.artifacts/m0/backend-20260909T065810797302Z`; frontend build/Ruff pass. Original latency failure,
Windows shared-temp failure and initial cleanup-test stdout fixture failure remain saved.

Harness review fixed lost timeout output and direct-process-only cleanup. Browser output now
streams to a file, process trees are owned/stopped, and a real timed-out child-process test passes.
The integration wrapper uses unique workspace temporary directories and a 420s bound for the
larger fixtures. The browser runs real Vite→FastAPI→PostgreSQL, with no response interception,
provider execution or application-data seeding. This does not complete imports, labels or M1–M6.
Next authorized slice: confirmed repetitive-text provenance and context-selection RAG defects.
