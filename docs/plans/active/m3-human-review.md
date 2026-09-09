# M3 — governed human review

## Execution brief

Outcome / gates: complete the connected REVIEW path after a cited development draft, advancing
ROUTE/JOB/TRACE/UX without claiming semantic AI quality. Deep correctness-sensitive work; root
owns implementation. Existing M1–M6 authority covers backend/frontend/migrations/tests and small
branch pushes; no paid API, merge, deployment or archived-service/data changes.

Baseline: workbench checkpoint `281b169`, built on durable support backend `8cff3bb`. Read root,
backend/support/frontend/docs guides, REBUILD_PLAN sections 4/8/9 and ACCEPTANCE. Current graph
ends at a draft; current state conflates execution and outcome. Real development contributions
are admin-attributed, not verified external inference or semantic policy detection.

## Connected implementation

- Separate execution state and response outcome. Preserve original message, generated draft,
  citations and drafting time; reviewed response and attributable decision are separate fields.
- Add one immutable decision per run/revision: actor, action, reason, expected draft hash/revision,
  edited response if any, payload hash and timestamp. Same actor/payload retries are idempotent;
  competing decisions yield one winner and one scheduled resume job.
- Operator/admin handles ordinary approve/edit/reject; policy-exception approval requires admin.
  Restriction comes from persisted routing classification, never the review request. Explicit
  development routing annotations exercise this boundary but do not prove semantic detection.
- Use a separate server-owned `review-v1` LangGraph continuation for the same run. The generation
  graph's existing completed checkpoints remain valid history. New drafts initialize a durable
  review interrupt; migrated old drafts stay unapproved and lazily initialize this continuation.
  A saved development handoff response cannot resume the review interrupt. Only a stored,
  authenticated decision matching the draft identity can do so. Never edit raw checkpoint state.
- Submission atomically stores decision and job. Publication checks workspace → run → current
  lease, cancellation, original requester/contributor/reviewer roles, revision and draft identity.
  Approval revalidates every contextual source. Rejection can finish despite stale evidence and
  publishes no customer response. Preserve decisions if later publication fails.
- Add review controls to the selected message, not another page/editor. Keep draft and final
  response distinct, progressive history, viewer read-only and clear pending/failure feedback.

Linked retries, clarified input and full policy/claim validation are subsequent slices. Do not
silently declare them complete or overwrite the immutable original to make retry easy.

## Independent design review

Reviewer identified the two-interrupt hazard: the existing `handoff.response` resume condition
would incorrectly consume a later human-review interrupt. Separate versioned continuation and
decision eligibility avoids that. Existing END checkpoints cannot be migrated by appending a
node; old drafts enter the explicit review continuation without rerunning generation.

## Verification and finish

Real PostgreSQL: ordinary operator approval/edit/reject, preserved draft, denied viewer/exception
approval, concurrent/conflicting decisions, cancellation/revocation after submission, stale sources,
review-checkpoint/publication replay and v1-draft transition. Real worker restart at the durable
review wait; real browser approve/edit/reject and permission views. Preserve failures; never weaken
assertions. Independently review implementation and docs, refresh mapped receipts, pass affected
checks, commit/push/inspect CI. Record limitations and next connected slice in STATUS.

## Current verification and repairs

- First broad run `.artifacts/m0/integration-20260909T020551013588Z`: 68 passed, four failed.
  Three new tests incorrectly tried to update a nonexistent membership; setup now inserts it.
  Malformed-rerank test had not proved successful indexing; added job/chunk diagnostics without
  weakening its expected error. That intermittent cause remains unestablished.
- Next broad run `.artifacts/m0/integration-20260909T021324937320Z`: 72 passed, one failed.
  New failed-review-resume test exposed empty `next` alongside a retained interrupt/task error.
  Empty `next` is not terminal proof. Focused failures at `021543471751Z`, `021630456305Z` and
  `021715086121Z` are preserved under the same integration artifact prefix. The first attempted
  fix missed the empty-next branch; test snapshot diagnostics identified it precisely.
- Recovery now checks tasks/interrupts, retries failed nodes with supported `invoke(None)`, and
  revalidates the stored decision before resuming a recreated interrupt. Publication still checks
  exact decision/action/response and authority. Independent review confirmed installed LangGraph
  pending-write semantics; the same correction covers development-generation continuation.
- `.artifacts/m0/integration-20260909T022005010569Z`: four focused cases passed: failed review
  resume, failed development resume, old completed draft migration, queued legacy contribution.
  Old drafts retain evidence and require admin approval; generation does not rerun for review.
- Connected review UI and generated API contract build successfully. Real browser checks,
  worker restart, broad regression and final independent review/freshness are pending.

### Connected browser and timing investigation

- `.artifacts/m3/review-ui-first`: six browser cases passed (EN operator approval, JA edit,
  ZH rejection, exact sources, cancellation, viewer widths/focus, delayed navigation). Desktop
  Japanese review and 360px Chinese source screenshots inspected. This run precedes the editor
  transition repair below and the additional policy-exception browser case.
- Chrome run `a98f393d-1b37-453b-ab66-e3a1e938f6ae` used actual retrieved policy and a Codex-authored
  development answer. Confirmed two review checkpoints before restarting the real worker at
  02:31:23 UTC; browser approval then produced one decision/job and preserved draft/final.
  `.artifacts/m3/restart-review-result.json` stores the database result. This is restart at a
  durable wait, not a mid-provider process-kill test.
- Broad `.artifacts/m0/integration-20260909T022607607844Z`: 74 passed, two failed (missing third
  indexed version and handoff elapsed -544.771ms). No scheduler root cause established. Expanded
  indexing preconditions now capture job state/error/availability, database time, active version
  and chunk count. Do not retry or sleep to conceal a failed claim.
- Independent 1,200-sample/61.68-second clock observation found no backward jump; evidence
  `.artifacts/m3/clock-observation/samples-20260909T023000Z.log`. An intermittent clock adjustment
  outside that window remains possible, not proven. Host settings and scheduling are unchanged.
- Handoff timing now reports null elapsed plus explicit `clock_anomaly` for reversed timestamps,
  preserving raw timestamps. The old nonnegative-only assertion changed to verify exact
  timestamp/status/value consistency; new -1/0/90-second API tests require explicit anomaly
  reporting rather than zero clamping. This does not establish the negative timestamp's cause.
- Independent UI review found edit text initialized before a polled draft arrived. ReviewPanel
  now remounts only on draft identity/revision changes; browser regression checks initial wording
  and retained edits across a successful poll. Final browser and broad verification remain pending.

### Final slice verification

- 79 PostgreSQL tests passed: `.artifacts/m0/integration-20260909T023808458445Z`.
- 16 unit tests passed: `.artifacts/m0/backend-20260909T023856099226Z`.
- Seven browser journeys passed: `.artifacts/m3/review-ui-final`, including the edit-arrival/poll
  regression and restricted policy-exception approval. Build/Ruff and four component tests pass.
- Six baseline browser cases passed: `.artifacts/m3/baseline-final`. Final narrow operator review
  screenshot inspected; source excerpts, response/draft separation and responsive controls remain usable.
- Backend and timing reviewers report no remaining blocking finding. Timing reporting is repaired;
  the timestamp and intermittent claim/indexing causes remain explicitly unresolved.
- Final documentation review, prep checks and branch checkpoint follow these results. Linked
  retries/clarification and remaining M3 gates are subsequent authorized work, not completed here.
