# M1 — runnable isolated foundation

Status: active. Entire M1–M6 goal authorized on 2026-09-08, starting at `2c292d0`.
Session work began 13:34 UTC; save a resumption checkpoint by 17:34 UTC if unattended.
Root/local guides and REBUILD_PLAN own constraints. One implementation owner.

## Execution brief

Outcome: a fresh local install serves a usable login/workspace shell, enforces membership and
role boundaries, and exposes enough logs/tests for Codex to demonstrate and repair failures.
Gates: BOOT, AUTH, TENANT and the M1 portion of UX/TRACE. Product AI is M2 onward.

Authority: normal working-branch commits/pushes and offline isolated services/tests allowed.
No old services/data changes, main/archive updates, merge/deploy or paid API calls.
The user has no API currently. This Codex session cannot be the runtime provider; implement
real provider interfaces with explicit deterministic offline verification, leaving live gates open.

Approach: first enforce the preparation rules already reviewed, then a pinned backend with
PostgreSQL migrations, health and structured request logs, then session auth/workspace APIs,
then the actual frontend and browser acceptance. Build only needed module boundaries.
Risks: authentication/session/CSRF design, last-admin concurrency, leaked foreign workspace data,
Windows runtime tooling, unproven live provider. Use real PostgreSQL for database claims.

## Slices and acceptance evidence

1. Harness: discover all nonignored Markdown, check local links and instruction limits, add
   broken-link/size regressions and Linux/Windows CI. Verify locally and inspect remote CI.
2. Runtime: isolated Compose database/API, lockfile, migrations, health/readiness and request
   logs. Verify fresh migration, healthy response and controlled database-unavailable recovery.
3. Auth/workspaces: server sessions, login/logout/expiry, roles and last-admin protection.
   Verify successful/denied requests, foreign IDs and concurrent demotion with PostgreSQL.
4. UI: minimal responsive workbench shell/login/workspace navigation, failure states.
   Verify actual browser login, workspace denial, keyboard/viewport behavior and request logs.
5. Independent boundary review, repairs and M1 evidence checkpoint; continue to M2.

Commands are added to RUNBOOK only when executable. Capture commands, exit codes and artifacts
for each slice. Gate completion requires actual behavior; documentation is not evidence.

## Progress and decisions

- Initial state: clean `codex/fresh-start`, no backend application. M0 probe/fixtures exist.
- Harness slice: 13 local preparation tests passed, including nested guides and failure cases.
  Pushed `a8308bf`; CI run `34233220196` passed Windows and Ubuntu jobs.
- M2 access: no API available; $0 spending. Continue offline work; live quality remains unverified.
- User clarified development AI: add a Codex-assisted request/response handoff in M2 so the app
  can consume answers produced in this coding session through its provider contract. Label its
  provenance accurately; it does not prove API connectivity, embeddings, latency or billing.
- Runtime slice: fresh database/vector migration and API startup passed; real outage returned
  readiness 503 while liveness stayed 200, then readiness recovered to 200. Request IDs matched
  server logs. Two backend tests and lint passed; final source-linked verification/push follows.
- Foundation pushed as `2dd4048`; CI run `34234381342` passed.
- Auth/workspace APIs: PostgreSQL-backed revocable sessions, CSRF/Origin validation, Argon2,
  bounded throttling/cleanup, membership enforcement and serialized last-admin writes implemented.
  Independent security review found no P1 bypass; fixed malformed-CSRF handling, cleanup and
  missing delete coverage. Also made pre-login token consumption atomic. Follow-up review
  identified cleanup/counter races; replaced read-then-increment with atomic upsert/returning,
  guarded cleanup against refreshed rows and added concurrent cleanup regression. All 14 real
  PostgreSQL integration tests passed. Two unit tests and lint pass; final runtime rebuild/push follows.
- Retained failure: initial integration run had six failures because engine connect options
  overwrote test search_path. Preserved URL options and added explicit migration transaction
  commit; integration cases then passed. Final suite includes throttle-window regression.
- Next: verify/push auth slice, inspect CI, then provision synthetic users and implement browser UI.
- User requires real RAG retrieval without API access: M2 will use a real local multilingual
  embedding model, actual PostgreSQL vectors and document-derived retrieval. Only generation
  API transport is simulated; Codex assists with genuine answers from the retrieved evidence.
  This explicitly permits the local embedding dependency needed for development; no GPU is required.
