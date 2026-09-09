# M3 — human clarification requests

## Execution brief

Outcome / ROUTE/REVIEW/DATA/UX: an operator/admin reviewing a draft can request specific customer
details, preserve the draft/decision, then process the customer's reply as a fresh linked attempt.
Current review only approves, edits or rejects; adding customer details already creates a child.
Deep authorization/workflow extension; root owns backend and connected UI. Read root, backend,
review, frontend and docs guides. Baseline `13322ca` recovery checkpoint is pushed; CI passed.
Existing M1–M6 authority, no paid API/external sends/merge/deployment; stop at 04:44:58 UTC.

## Decision and implementation

- Add an explicit `clarify` action with a required question in the immutable decision response.
  Reuse existing storage; no additional table. Clarification never populates approved response.
- Approve/edit retain current-source and policy-exception admin checks. Reject/clarify are
  operator/admin actions which approve no answer. Preserve requester/creator/contributor/reviewer
  eligibility, draft identity, revision, payload idempotency and fenced publication checks.
- Update both graph output and publication validation. Only successfully published clarification
  has outcome `clarification_needed`; a submitted-but-failed/cancelled decision stays history.
- Display the question as the current next step after publication, with the unapproved original
  draft collapsed. Label the action/request clearly; nothing is sent to a customer automatically.
- Existing added-customer-details flow creates fresh retrieval/graph/review state. Do not append
  the administrator's question as customer input or reuse any previous approval.

## Verification and independent review

Independent design review completed: explicit action sets, successful-publication UI gating,
exact checkpoint question matching and fresh child context are required. Test operator policy
exception/stale-source clarification, viewer/foreign denial, missing question, competing decisions,
cancellation/revocation before publication, replay and question→details→fresh retrieval. Exercise
the actual browser, regenerate types, verify affected/full regressions, update docs/receipts,
commit/push and inspect CI. Semantic policy/language validation and full release remain open.

## Current evidence

- Recovery baseline CI `34308144856` passed. Its preparation receipt:
  `.artifacts/m0/prep-20260909T034154254646Z`, 35 passing checks.
- Eight focused real PostgreSQL cases passed, including clarification and both approval/clarification
  checkpoint replay: `.artifacts/m0/integration-20260909T034756729890Z` (35.98s).
- The result rendering was separated into a cohesive `RunResult` component instead of extending
  a nested response branch in `RunView`. Published questions are primary; cancelled/failed/queued
  decisions appear only as history. Four publication-state component cases and all nine component
  tests pass, together with regenerated API types and TypeScript/Vite build.
- All nine browser journeys pass in `.artifacts/m3/clarification-workbench-ui` (2.3 minutes),
  including Japanese policy-exception clarification and fresh customer-reply retrieval. The
  360px question/draft/source screen was inspected without overlap. Actual Chrome run
  `7aee3f1a-94e2-4a18-bd71-505f8b1c53e4` also published an internal question and started a child
  from a synthetic reply. No external message was sent.
- Full run `.artifacts/m0/integration-20260909T035301713441Z`: 105 passed, two setup failures.
  Diagnostics captured queued availability `03:55:42.576412` after a subsequent database-clock
  reading `03:55:40.963361` (1.613051s earlier); already-finished jobs also had future availability.
  This proves an immediate claim was not due at observation. It supports clock regression but
  does not identify the host/VM mechanism or prove every earlier failure had the same cause.
- Independent review approved a test-only readiness wait: intended workspace/kind, queued,
  attempts zero, verified future availability, five-second monotonic bound, closed polling
  transactions and exactly one worker execution. No timestamp edits, failed-job retries or
  production scheduling changes. Local `job-readiness.jsonl` retains observed waits.
- Five readiness/previous-failure cases pass in `.artifacts/m0/integration-20260909T040026637272Z`.
  Tests cover future/due/absent/retry/deadline behavior; the future fixture waited 187ms without
  claiming or changing the job.
- Final unchanged-source regression: 110 PostgreSQL tests passed in 203.86s,
  `.artifacts/m0/integration-20260909T040250637259Z`. Its readiness artifact records the synthetic
  future-job test waiting 188ms; no additional wait was recorded. This does not prove clock
  stability or establish the cause of every earlier intermittent setup failure.
- `.artifacts/m3/clarification-live-result.json` verifies the original completed question and
  child `54ce976a-95b2-45b4-bafe-7ca15e2e00d5`, with fresh trace and no inherited decision/draft.
  Backend/application sources were unchanged after the final full regression; subsequent edits
  close documentation and checkpoint bookkeeping. Full M1–M6 release gates remain incomplete.
- Independent source/UI review found no blocking issue. Stale review API actions and blanket
  source-revalidation wording were corrected to match the explicit approve/edit distinction.
- Completed checkpoint `7c7abf3a17e8e1856ef6498dc9f0c9c231cb20d8` is pushed; CI `34310112516`
  passed. Six independent documentation receipts and 35 preparation checks passed in
  `.artifacts/m0/prep-20260909T041254188886Z`. Overall M3/M1–M6 remain incomplete.
