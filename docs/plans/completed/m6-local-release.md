# Local release packaging — completed verification slice

Outcome BOOT/UX: run the built React UI and API at one local origin, with a worker and
PostgreSQL and no Vite process in the release stack. Root owns implementation. Read backend,
frontend, infrastructure and scripts guides. Preserve development and archived services/data;
no paid calls, external deployment or RAG tuning.

Use an explicit static directory, serving only its assets and index for known navigation
routes. API and missing-asset errors stay errors; deny private files and traversal. Build
locked frontend assets into a separate non-root release image. Isolate Compose namespace,
volumes and loopback port, with explicit trusted origins and separate generated credentials.
Fail configured startup if assets are absent. Never silently fall back to a dev server.

Verification: static-route unit tests (GET/HEAD, MIME/cache, API404, private/traversal denial,
missing build); actual fresh Compose migration/bootstrap; real browser login, nested refresh,
new clarification through worker, logout and authorization/CSRF denial with Vite absent from
the release stack. Record source fingerprint, runtime identity, logs, screenshots and limits.
Independent security review and owning-doc freshness review precede checkpoint.

The initial independent design review requires strict SPA routes, symlink containment,
explicit origins, non-shared database/model volumes and a fresh browser context. This proves
local packaging/clarification flow, not real-provider quality or complete release readiness.

## Evidence and repairs — 2026-09-09

- Fresh image/database/model volumes: `.artifacts/m0/release-up-20260909T111652893904Z`;
  separate credentials `.artifacts/m0/release-seed-20260909T111804722155Z`.
- Actual EN/JA/ZH CPU embedding/reranking after explicit model provisioning:
  `.artifacts/m0/release-prepare-model-20260909T111826757372Z`. This is not a quality gate.
- Initial three browser checks pass21s at `.artifacts/m6/release-browser-20260909`.
  Review identified invented-UUID evidence overclaim; final suite uses the private account's
  actual accessible workspace before asserting viewer denial. Three checks pass8.9s at
  `.artifacts/m6/release-browser-final-20260909`.
- Two knowledge journeys pass16.9s at `.artifacts/m6/release-knowledge-20260909`: real upload,
  CPU indexing/search, exact source, replacement failure, withdrawal/restore and viewer/mobile.
  Root inspected360px clarification and desktop retrieval screenshots.
- `.artifacts/m6/release-runtime-20260909.json` records healthy container/image identities and
  disjoint database volumes. API/worker use workbench UID10001; runtime has no Node executable.
- Initial direct unit run hit shared Windows temp access denial. First wrapper repair missed
  the parent directory (47 passes/2 errors, backend-20260909T111154717657Z); parent creation fixed.
  Next run found duplicate cache-control (49 passes/1 failure, backend-20260909T111256283014Z).
  MutableHeaders now preserves explicit policies and defaults API responses to no-store.
  Final52 units pass at `.artifacts/m0/backend-20260909T111449045956Z`; Ruff/format pass.
- Full PostgreSQL:143 pass/1 unclassified pre-dispatch timeout in
  `.artifacts/m0/integration-20260909T112103331925Z`. The kill/reconciliation assertions did not run.
  A lightweight child entrypoint now retains startup phases, bounded stack, exit code and scoped
  trace/ledger statuses. Focused recovery9 pass24.27s at
  `.artifacts/m0/release-recovery-20260909T113036495729Z`: imports14.625s, dispatch14.719s, then
  actual termination/concurrent reconciliation leave trace and call uncertain. The20s deadline
  stayed unchanged. This does not establish the precise cause of the original timeout.
- Independent review required explicit release-model preparation, missing-index/assets checks
  and migration-failure fencing; all added. The failure-injection test passes. Outer forced
  termination cleanup remains unverified. Full regression rerun and final docs review pending.

Fresh npm install also exposed js-yaml advisory GHSA-2883-xcg3-v3hh through development-only
openapi-typescript/Redocly. Production-only audit reports zero findings. A scoped override to
js-yaml4.3.2 is the next separate dependency repair; do not run a broad audit-fix upgrade.

Final full PostgreSQL rerun:144 passed in360.11s at
`.artifacts/m0/integration-20260909T113404211217Z`. The real process-kill case reached dispatch
at17.562s (imports17.437s), terminated and reconciled to uncertain as required. This confirms
the revised diagnostic harness passed, while retaining the earlier unclassified timeout.
Final source review found no technical blocker; semantic review/receipts and prep close the slice.

Minor follow-up from final review: child-test diagnostics run before pipe closure in finally.
A diagnostic database/filesystem failure could mask the original assertion and skip closing
pipes; nested cleanup would improve this failure path. Normal cleanup and recovery passed.
This is a harness limitation, not evidence of a product recovery failure.
