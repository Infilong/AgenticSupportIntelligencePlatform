# Browser CI and shared startup checks

## Problem
The existing CI compiled the frontend and ran SQLite backend tests without exercising the
application in a browser. Local verification also assumed container startup meant HTTP ready.

## Implementation
- `.github/workflows/ci.yml` adds an isolated Compose browser job with PostgreSQL, migrations,
  explicit HTTP startup checks, Chromium journeys, logs, artifacts and disposable-volume cleanup.
- Backend installation uses the committed uv lockfile with `--frozen`.
- `scripts/wait_http.py` owns bounded HTTP startup polling, shared by CI and the Windows runner.
- `scripts/tests/test_wait_http.py` tests retry, timeout, status-code and invalid-input behavior.
- `scripts/verify.ps1` records tooling, source-size and readiness checks alongside existing runs.

No product routes, business rules or database schema change in this ticket. Browser tests use
synthetic accounts and mock providers; no model key is supplied to the stack.

## Validation and limits
All 13 tooling tests pass. The readiness command succeeds against the live local API/frontend
and exits 1 against an unavailable endpoint. Workflow YAML parses successfully. End-to-end
local runner evidence is recorded in the testing guide.

Remote GitHub execution and required branch checks remain unverified until the change is
published and run. The browser job proves only its existing journeys on PostgreSQL; it does
not replace dedicated concurrency tests, migration upgrade/rollback tests, or production
readiness checks. The CI stack still uses development images and synthetic credentials.
