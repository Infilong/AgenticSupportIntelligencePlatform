# Historical retrieval results in Quality

## Execution brief

Continue the authorized M1–M6 goal, with RAG tuning deferred. Advance TRACE/UX and the M5
evaluation presentation requirement; this does not complete EVAL's four generation pipelines.
Deep boundary: persisted report provenance and workspace authorization. Root owns implementation.
Read root/backend/frontend/quality/scripts/evals/docs guides; preserve unrelated work.

Register the existing completed retrieval-strategies-v1 report using an explicit local command.
Require an administrator of its actual primary workspace, validate every referenced trace belongs
there, retain an immutable allowlisted snapshot and report/source/corpus hashes. Reject partial,
invalid or inconsistent reports; preserve failed measured cases. Duplicate registration is idempotent.
Do not publish raw reports, foreign-workspace probes/documents, expected answers or local file maps.
Expose bounded workspace-member list/detail reads and progressive Quality UI: strategy comparison,
EN/JA/ZH denominators, p95, failures and existing authorized trace inspection. Historical results
are not current measurements, confidence scores, held-out quality or generation verification.

No new execution queue, model calls, RAG tuning, upload UI, provider integration or cloud service.
No paid API or external actions beyond verified branch commits/pushes. Stop at the active window.

## Verification

- Real PostgreSQL migration/register/read: idempotency, malformed/partial rejection, trace mismatch,
  viewer/foreign/revoked denial and bounded list/detail. Projection checks keep honest denominators.
- API types, frontend tests/build; actual browser populated/empty/failed/denied states and workspace
  switching, trace inspection, 360/768/1440 layouts. Retain screenshots and failures.
- Independent security and semantic documentation review, preparation checks, small commit/push.
- Register the existing real local report without rerunning its measurements; report measured-source
  fingerprints and distinguish registration time from unknown execution timestamp.

## Results

Implemented registration, migration0014, bounded member reads, generated API contract and Quality
views. Initial10 PostgreSQL checks passed at
`.artifacts/m0/historical-evaluations-20260909T121125761486Z`. First actual standalone registration
failed with NoReferencedTableError for users: API-test imports had masked the missing mapping.
The transaction rolled back. Service now loads/checks the actor explicitly; a real fresh-process
CLI/idempotency test closes that gap.11 focused checks pass at
`.artifacts/m0/historical-evaluations-20260909T121644152361Z`. Initial CLI traceback is retained in
the task tool output; runtime setup logs are `.artifacts/m5/runtime-up.log` and `runtime-up-fixed.log`.

Independent security review found passed cases could contradict failed fact_results. The projection
now validates bounded strict fact booleans against the frozen scorer's groups/facts/leakage/bound
formula;13 projection tests pass, including legitimate failed facts with complete groups.
Independent UI review found relative API URLs in the browser harness and an arbitrary empty
workspace assumption. URLs are absolute and the empty workspace precondition is checked through
authenticated reads. Actual layout/browser verification remains pending.

42 frontend tests pass and TypeScript/Vite build passes after generated API types are refreshed.
An initial ad-hoc schema export lacked Settings, leaving stale types and causing the first build
to fail. The documented database-free app.export_schema command succeeded; generation/build
then passed. Failed output is in task tool history; no application behavior was relaxed.

Dependency repair is pushed as b35214e; CI34348039265 passed.46 preparation checks pass at
`.artifacts/m0/prep-20260909T115108488972Z` for that earlier slice. Chrome remains signed out pending
the user's login; isolated test-browser journeys continue with existing synthetic test credentials.

## Verified checkpoint

The actual report registered as129fd440-6ace-4ee6-8353-c2f22526a740 in its existing primary
workspace245755f5-e947-4d6c-97dc-062abd10aeda. Identity is retained at
`.artifacts/m5/registered-report.json`; the source report was not changed or rerun.
The first browser run had one pass and one harness failure: a foreign login correctly retained
the protected deep link and showed Workspace unavailable, while the test expected a workspace
selector. The test now asserts denial, uses Back to my workspace, then verifies API/deep-link404.
The initial screenshot also revealed inherited column navigation; scoped row layout fixes the
desktop Quality buttons and has browser coverage. No permission assertion was removed.
Initial evidence: `.artifacts/m5/evaluation-browser-20260909`.

Final three real browser journeys pass in11.5s at
`.artifacts/m5/evaluation-browser-fixed-20260909`: actual comparison, failed Japanese trace,
filtered/excluded cases, workspace switch/empty state, synthetic503 retry, real foreign404,
and existing settings/usage behavior.360/768/1440 screenshots plus the final overview were
inspected; no page-level overflow or page errors were observed in the comparison journey.
65 backend units pass at `.artifacts/m0/backend-20260909T122655401468Z`.
155 full PostgreSQL checks pass in356.76s at `.artifacts/m0/integration-20260909T122535921561Z`.
42 frontend tests and TypeScript/Vite build pass after the final UI repair. Ruff passes.
The upstream AnyIO deprecation warning remains visible.

Independent security review confirms the fact/CLI repairs; independent UI review found no
additional blocker after its harness corrections. Semantic review identified two stale
usage-only claims in architecture/runbook; both are corrected. All six independent receipts
are renewed and freshness is clean.46 preparation checks pass at
`.artifacts/m0/prep-20260909T123445042611Z` before this evidence-only completion note.
This completes the bounded historical-results slice, not M5 generation pipelines or the full
release goal. Next: five concurrent operator sessions and bounded ingestion in the isolated
built release, recording the actual local workload and explicit development-provider limits.
