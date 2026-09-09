# M3 — linked retries and clarification

Completed slice: committed/pushed `2e2054f`; CI `34306686806` passed. Full release remains open.

## Execution brief

Outcome / gates: an operator/admin can retry a failed/cancelled attempt or add customer details
without losing the original message, prior drafts, decisions or evidence. Advance M3 DATA/ROUTE/
JOB/UX under existing M1–M6 authority. Deep persistence/authorization work; root owns implementation.
Baseline `497b160` includes governed review. Read root, backend/support/review, frontend and docs
guides; REBUILD_PLAN sections 4/8/9 and ACCEPTANCE. No paid API, merge or deployment.

## Connected slice

- Add immutable per-run processing input, creator, parent and sequence. Migrate existing runs
  from their original message. Keep one message record; new attempts receive distinct jobs,
  graph threads, retrieval records, development contributions and review decisions.
- Retry preserves the previous processing input; clarification appends bounded additional
  customer details. Preserve every earlier input and never reuse its approval or stale evidence.
  The combined input retains the existing 1,000-character retrieval boundary; reject overflow
  explicitly instead of truncating. Local embedding token limits still apply. Independent design
  review caught a proposed larger snapshot exceeding the existing retrieval contract.
- Authenticate before scoped lookups and idempotency checks. Serialize by workspace/message;
  only the latest terminal or paused attempt may create a child. Explicitly supersede
  an unreviewed draft through cancellation before creating a child; reject concurrent stale
  submissions. A bounded per-message attempt count prevents an unbounded lineage.
- Bind submission keys to actor/action/parent/details; same payload retries return the same
  child. Database constraints prevent cross-workspace lineage and duplicate sequence numbers.
- Keep original requester and current attempt creator eligible before processing/publication.
  A new retry does not inherit another actor's permission. Approval checks remain unchanged.
- Inbox returns one latest attempt per original message with a consistent total. Selected detail
  exposes bounded chronological attempt links and added input. Keep retry/clarification in the
  existing view with one small progressive form; viewers inspect history but cannot mutate it.

## Verification

Real PostgreSQL: original/history preservation, fresh retrieval, idempotent retry, conflicting
child submissions, revoked/foreign/viewer denial, active-run conflict, sequence/latest-list and
review isolation. Real browser: `w` → add meaningful details → retrieval/draft, cancelled → retry,
history navigation and denied controls. Independently review source/docs; regenerate API/factual
references, run affected checks, record freshness and commit/push/inspect CI.

Human request-for-clarification wording, full policy/semantic validation, imports/evaluation and
the remaining process-kill matrix are separate remaining gates; this slice cannot claim full M3.
Stop at the documented work-window boundary if unfinished and preserve an exact checkpoint.

## Current repairs and evidence

- Initial focused run `.artifacts/m0/integration-20260909T025304736625Z`: six passed, one failed;
  concurrency fixture omitted explicit checkpoint initialization. Fixed setup, not runtime setup.
- Next `.artifacts/m0/integration-20260909T025459570426Z`: nine passed, one failed; attempt-limit
  fixture passed an existing UUID to the text-only UUID constructor. Corrected test conversion.
- Eleven focused cases passed: `.artifacts/m0/integration-20260909T025836037231Z`. Build/Ruff pass.
- Independent review found retry could treat the application's clarification label as meaningful
  customer input. Validation now derives the latest actual input from bounded immutable lineage,
  constrained to this attempt's sequence; newer details cannot change an earlier attempt.
  Both direct and cancel/retry variants pass in `.artifacts/m0/integration-20260909T030224457925Z`.
- Migration `0009_attempts` ran in the isolated runtime. Full PostgreSQL regression passed all
  91 cases in 161.33s: `.artifacts/m0/integration-20260909T031006335983Z`, unchanged snapshot.
- Browser `.artifacts/m3/linked-attempt-ui`: seven passed, one failed. The new linked journey
  passed, including real retrieval, cancellation/retry, history and viewer denial. Its 360px
  screenshot was inspected without overflow/overlap. The older viewer test depended on an
  existing first-page unreviewed draft; no such row existed. It now creates its own real draft
  and navigates by its exact URL, retaining source/focus/width assertions.
- Independent backend review found no remaining blocking issue after the latest-input fix.
  UI review found a Unicode counter/HTML UTF-16 maxLength mismatch. The form now uses explicit
  code-point validation and visible overflow feedback, with submission disabled above the
  server limit. Emoji/supplementary Chinese regression, all five component tests, build and Ruff pass.
- Repaired viewer and linked-attempt browser cases pass in `.artifacts/m3/linked-attempt-ui-repaired`
  (two cases, 43.9s). This complements seven passing cases in the initial eight-case run; it is
  not one fresh all-green eight-case run. Narrow viewer/source and history screenshots inspected;
  actual Chrome showed all three attempts with the original preserved. Backend sources did not
  change after the 91-test run; subsequent UI/test/docs edits change the whole-repo fingerprint.
- All six independent documentation receipts and 35 preparation checks passed before commit.
  The preceding unstaged-plan-move inventory failure and repair are retained in the next recovery
  record. Earlier intermittent timestamp/claim causes remain open. This slice does not complete M3.
