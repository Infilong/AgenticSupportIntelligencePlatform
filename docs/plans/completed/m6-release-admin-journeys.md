# Packaged administration and session journeys

## Execution brief

AUTH/DATA/TRACE/UX: verify existing admin/session/settings/import/inbox flows against packaged
release assets. Normal bounded QA slice; root owns only four harness runtime overrides and
owning evidence/docs. Root/frontend/docs guides apply. Reuse established ASI_APP_BASE_URL and
ASI_DEMO_CREDENTIALS overrides, retaining development defaults. No product/provider/schema change.

Run app.spec.ts, settings-usage.spec.ts, message-import.spec.ts and inbox-views.spec.ts together.
Verify actual sign-in/out, last-admin denial, viewer denial, lost-session/outage recovery, settings
restore, recorded usage at three widths, invalid/valid multilingual import, labels, explicit
processing and filtered navigation. Retain synthetic test records. Do not print login snapshots.
Injected faults prove UI recovery, not real expiry/revocation or a complete release security gate.
Inspect screenshots/logs and final reports, independent review, types/prep, then commit/push.
Stop at14:58 UTC. Computer Use remains stopped; this is independent headless app QA, not nativezoom.

Development and packaged readiness both returned ready/provider_mode mock before the run.
Status navigation is committed/pushed asf1cb7ad; its CI is not yet observed. RAG tuning remains
deferred; these journeys reuse the release's real models/long-policy corpus and fixed providers.

## Evidence and review repair

All nine initial packaged cases pass in35.2s at `.artifacts/m6/release-admin-20260909`.
Independent review identified a pre-existing settings-harness cleanup gap: a failure after saving
could leave the synthetic workspace default changed. Added an authenticated same-workspace cleanup
boundary that runs after success/failure and preserves both flow and cleanup errors. The existing
assertions remain; no application code or authorization changed.

Final settings rerun passes both cases in7.3s at
`.artifacts/m6/release-settings-cleanup-20260909`: the original settings/usage journey and a new
real regression that changes the language, throws an injected flow error, restores via API, then
reloads and verifies the original value. Other eight unchanged initial cases remain valid; this
is aggregate coverage of ten distinct cases, not a final ten-case all-green suite.

Standalone strict TypeScript passes after cleanup repair. Root inspected mobile imported-message
and final usage screenshots; width checks cover360/768/1440. Bounded log-summary.json in the final
directory records251 HTTP200,1 HTTP201,3 HTTP202,2 HTTP204 and expected401/403/404/409/422 denial
or invalid-input responses. No HTTP5xx or worker ERROR/Traceback markers were found in that window.

The arbitrary unavailable-workspace UUID in app.spec.ts does not prove actual foreign data exists.
Documented it as UI unavailable-workspace handling; real foreign denial remains covered separately
by the prior release smoke/PostgreSQL tests. Cookie clearing and injected outages likewise do not
establish real expiry/revocation or complete the security gate. No nativezoom/generation claim.

Final review found three pre-existing response/click pairs could orphan a response rejection if
the click failed. Replaced them with one bounded helper that settles both operations immediately
and retains all errors. Final settings evidence `.artifacts/m6/release-settings-final-20260909`
passes both cases in7.5s; strict standalone TypeScript also passes. Earlier nine-case and cleanup
evidence is retained, not replaced. This is a harness reliability repair, not an app feature change.

Independent source and semantic-documentation reviews closed with no remaining findings.
All53 prep checks pass at .artifacts/m0/prep-20260909T144034446438Z; Chromium environment
verification passes at .artifacts/m0/browser-20260909T144047776655Z. Root also inspected the
final360px Settings screenshot with original English default. Navigation CI34363843198 passed.
This completion note follows verification and changes no mapped source or documentation contract.

Checkpointfd18e50 is pushed. GitHub CI34365353115 passed all five jobs: Windows/Linux
preparation, backend PostgreSQL integration, frontend browser tests and packaged release smoke.
M5 generation-path assessment remains unimplemented, with explicit live/no-spend limitations.
Final window handoff updates STATUS only; no further application or harness edits follow.

Final handoff wording is independently reviewed;53 preparation checks pass at
.artifacts/m0/prep-20260909T144941203289Z. This note records that result without changing the
reviewed current contract. The full goal remains active/incomplete at the window boundary.
