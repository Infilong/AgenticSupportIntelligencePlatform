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
