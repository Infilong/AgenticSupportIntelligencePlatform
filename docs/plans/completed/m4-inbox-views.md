# M4 — focused inbox views

## Execution brief

Outcome / UX/DATA: find the next customer message needing action without reading every row.
Normal bounded API/UI slice within M1–M6, root implementation owner. Read root/backend/support,
frontend/docs guides. Baseline `7c7abf3` human clarification is pushed; 110 PostgreSQL tests,
nine browser journeys, nine components/build and 35 preparation checks passed.
Stop at 04:44:58 UTC; no imports, model changes, paid calls, deployment or permission changes.

## Contract and approach

- Server-valid views: all, attention, ready, processing, failed. Apply search, workspace and
  view to the same latest-attempt query for both totals and paginated rows.
- Attention: development handoff, human review, or completed clarification/missing evidence.
  Ready: completed approved response. Processing: queued/running, including the actual job
  state while a run remains queued. Failed: technical failure. Rejected/cancelled remain in All.
- Add one labelled view selector and clear filters action; reset pagination on filter changes.
  Preserve selected detail if the message leaves a filtered result after processing.
- Show completed outcome instead of generic Completed. Bound the message rows' scroll region
  with visible keyboard focus; keep controls outside it and retain responsive detail navigation.

## Verification and completion

Real PostgreSQL projection tests cover all states, search/count/pagination, latest attempt,
invalid view and foreign/viewer authority. Browser exercises filtering, selection, clearing,
empty results and 360/768/1440 widths. Regenerate API types, run relevant regressions/build,
independently review source/docs, update freshness, commit/push and inspect CI.
No claim of completed imports, full UX or M4 release from this slice.

## Evidence and repairs

- Baseline `7c7abf3` CI `34310112516` passed; preparation had 35 checks in
  `.artifacts/m0/prep-20260909T041254188886Z` and six independent review receipts.
- First integration command supplied a test path through PYTEST_ADDOPTS, which added to the
  wrapper's directory selection instead of narrowing it: 110 passed, three new fixture failures
  in `.artifacts/m0/integration-20260909T041805059938Z`. Use `-k` for focused wrapper selection.
- The fixture confused displayed execution states with persisted run states. The database correctly
  rejected direct running/failed SupportRun values. A second focused failure is preserved in
  `.artifacts/m0/integration-20260909T042327972231Z`. Inspection of migration `0008_reviews`
  established running/failed are projected from the job while the run stays queued. Corrected
  fixtures retain active, failed and failed post-draft coverage without schema/constraint changes.
- All three focused PostgreSQL view tests pass in 17.92s:
  `.artifacts/m0/integration-20260909T042451608052Z`. They cover matching counts/pagination,
  search escaping, latest-child movement, invalid views and viewer/foreign workspace checks.
- Independent review found shrinking result counts could strand a later page. The UI now clamps
  to a valid page. A component regression verifies 21→20 results and preserved selected detail;
  all ten component tests pass. TypeScript rejected a Playwright-only `exact` option in that
  component test; the option was removed and the TypeScript/Vite build passes.
- Initial browser evidence `.artifacts/m4/inbox-views-ui` retains an ambiguous search locator
  failure. The input locator now uses textbox role, distinct from the same-named search button.
  Back navigation uses the actual All messages label. Repaired browser verification is pending.
- Actual Chrome showed 15 approved-response rows in Ready and the empty Failed view, while
  preserving the selected child attempt. Sources and model/provider behavior are unchanged.
- Final independent source review found no remaining blocking issue. Full regression,
  responsive screenshots and final documentation review/checkpoint remain pending.
- The repaired browser run reached the 360px inbox and detected horizontal overflow
  (`.artifacts/m4/inbox-views-ui-repaired`). Screenshot inspection showed the administrator's
  third navigation link extending beyond the screen: mobile navigation forced one row.
  Mobile navigation now wraps; this preserves all links rather than hiding page overflow.
- Final full PostgreSQL regression: 113 passed in 217.67s against an unchanged source snapshot,
  `.artifacts/m0/integration-20260909T042732512966Z`.
- Repaired inbox browser journey passes in 20 seconds: `.artifacts/m4/inbox-views-ui-final`.
  Root inspected 360/768/1440 screenshots: wrapped mobile links, visible controls, bounded
  keyboard-focusable list, no horizontal overflow. Broader browser regression remains pending.
- Independent docs review caught stale architecture header and unfinished-filter claims;
  both corrected. Application sources remain unchanged after the final PostgreSQL run.
- All nine existing workbench browser journeys pass in 2.1 minutes:
  `.artifacts/m4/inbox-workbench-regression`. Combined with the separate new inbox journey,
  this covers all ten affected journeys. Final ten component tests and TypeScript/Vite pass.
  The accepted slice is ready for independent receipts, preparation and branch checkpoint.

## Next connected work

The independent import investigation confirms imported-but-not-started messages require changing
the current always-start creation and inner-join inbox assumptions together. Next window: define
bounded JSONL originals/language/labels and atomic import attribution, then connect import→select→run
through shared support processing. Cover workspace/role denial, whole-upload rollback, quota and
idempotency races, concurrent starts, original/label preservation and real retrieval in the browser.
Size/record/label bounds still need to be selected and documented before implementation; do not
silently truncate conversations or duplicate a processing path. No import implementation started.

## Closing checkpoint

Implementation checkpoint `8d7dd130ee6a1c171f41239276dd4afa62e1b966` is pushed; CI `34311767057`
passed. Six independent documentation receipts and 35 preparation checks passed in
`.artifacts/m0/prep-20260909T043813532131Z`. Four isolated services were healthy; all 199 jobs
were succeeded at the observation (development/review waits are separate persisted run states).

Final Chrome inspection of historical clarification `7aee3f1a-94e2-4a18-bd71-505f8b1c53e4`
found misleading generic copy directing a reply below even after a child exists. Removed only
that sentence; existing latest-attempt navigation remains. Ten component tests and the build
pass after this text-only correction. The full database/browser evidence above predates this
sentence removal, not a processing change. Final checkpoint CI may still be pending at cutoff.
The four-hour window ends 04:44:58 UTC; preserve this record and request resumed authority before
another implementation window. The full M1–M6 goal remains incomplete, not narrowed to this slice.
