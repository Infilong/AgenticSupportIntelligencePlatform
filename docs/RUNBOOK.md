# Local development runbook

## M1 API/database foundation

From the repository root, with Docker Desktop, Python 3.12 and uv installed:

```powershell
python scripts/manage.py init-env
python scripts/manage.py up
uv sync --project backend --frozen
python scripts/manage.py verify-backend
python scripts/manage.py verify-integration
uv run --project backend ruff check backend
uv run --project backend ruff format --check backend
```

`init-env` generates a database password in ignored `.env` without displaying it; existing
files are preserved. `up` starts only the fixed `asi-rebuild-v1` database, builds the API,
applies migrations, then waits for API health. It currently starts no worker or frontend.
Health endpoints: `http://127.0.0.1:8010/api/health/live` and `/api/health/ready`.
Readiness requires database access, current Alembic revision and pgvector extension.
`python scripts/manage.py migrate` reapplies pending migrations; `down` preserves volumes.

`python scripts/verify_runtime.py` performs a controlled stop/restart of only the rebuild
database, checks 200→503→200 readiness, API liveness during outage and request-log correlation.
It uses the default API port 8010; leave the default ports for this test. A finally block
restores the database. Evidence is saved under `.artifacts/m1/runtime-<timestamp>/`.
Request logs contain server-generated correlation IDs, route templates, status and duration;
bodies, query strings, arbitrary paths and credentials are excluded.

Backend unit evidence currently uses `.artifacts/m0/backend-<timestamp>/` via the shared
command wrapper; its scope is explicitly the named command, not full M0 or product acceptance.
The current TestClient dependencies emit upstream httpx/AnyIO deprecation warnings; tests
pass, but these warnings remain visible and are not application runtime failures.

`verify-integration` creates the dedicated `asi_rebuild_test` database if missing, migrates
temporary test schemas, and removes only those schemas after tests. It verifies sessions,
CSRF, roles/workspace denial and concurrent last-admin changes against real PostgreSQL.
It does not change the application database or any archived database. CI uses an ephemeral
PostgreSQL service and runs the same integration cases.

Session endpoints are `GET /api/session`, `POST /api/session/login` and `/logout`. Get a
session CSRF token first; unsafe requests require it in `X-CSRF-Token` and an allowed Origin.
The rebuild cookie is HttpOnly/SameSite=Lax, insecure only for the local loopback HTTP setup;
HTTPS deployment must enable secure cookies and configure exact trusted origins.
Sessions expire after eight hours or one idle hour; anonymous sessions after 15 minutes.
Login throttling uses persistent identity/client counters. New anonymous sessions prune expired
records in bounded batches and are rate-limited. Passwords and tokens must never enter logs.
User provisioning and browser login are the next M1 slice; no default admin password exists.

## Verified entry points

Use Python 3.12+ and Node.js 22+ on Windows. Docker Desktop must be running. Current checks
also verify Git, uv and Docker Compose. Use the repository's scripts from its root directory.

```powershell
python scripts/manage.py doctor
python scripts/manage.py verify-prep
```

Doctor checks tools, Docker daemon, registry metadata access and proposed port availability.
It never starts/stops a service or reads API keys. `doctor --offline` skips registry probes
and reports PARTIAL even when local checks succeed. Registry access is not model API access.

## Browser installation and verification

Install fresh dependencies from the lockfile:

```powershell
Push-Location frontend
npm.cmd ci --ignore-scripts --no-fund --no-audit
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Split-Path (Get-Location).Path -Parent) '.artifacts\browsers'
npm.cmd exec playwright install chromium
Pop-Location
python scripts/manage.py verify-browser
python scripts/manage.py evidence
```

On Linux/macOS, use `npm ci`, `PLAYWRIGHT_BROWSERS_PATH="$PWD/../.artifacts/browsers" npx playwright
install chromium` from frontend, then run the Python commands from the root. Linux browser
system-library installation may be needed; that platform has not been verified in M0.

Playwright is pinned to 1.63.0. The environment test verifies browser launch, multilingual
rendering and keyboard interaction on a synthetic page. It is not a UI/RAG acceptance test.
No personal Chrome plugin is needed. Each managed run saves its own logs, JSON result,
source fingerprint, screenshot and trace under `.artifacts/m0/browser-<timestamp>/`.

Preparation-test logs and metadata are under `prep-<timestamp>/`; doctor reports are timestamped
JSON files. `evidence` creates a summary for the current source fingerprint and rejects stale
test reports. Environment observations can expire independently when tools/ports/access change.
Repeated runs retain prior evidence. Deliberate failure-injection unit tests print failure-path
evidence messages; judge their unittest results, not those injected command exit codes alone.

## Sandbox and network behavior

The documentation checker is `python scripts/check_docs.py`; `verify-prep` runs it through
regression tests, including nested-guide broken links and instruction size failures. It scans
Git's nonignored Markdown list, not archived artifacts/dependencies. Inline local file links
are checked; remote URLs, fragment anchors and reference-style Markdown links are not validated.
The Verify workflow runs the preparation suite on Linux and Windows for branch pushes/PRs;
inspect the actual run before treating a configured workflow as passed CI.

The initial sandboxed npm metadata request failed with EACCES. An approved retry succeeded.
Registry downloads, Docker access, browser launches and Git writes may require tool approval
in Codex's execution environment. Treat these as access boundaries; do not bypass controls.
Prefer bounded requests and the existing automatic approval review over disabling safeguards.
No model API request or paid evaluation is part of M0.

## Preserved state and runtime isolation

Old HEAD: `c239c8d9c278f50da9b7869872345e9af09d06b1`, archive branch
`archive/previous-platform-2026-09-08`. Fresh root: `c70f254562463b8cf8bc342e30d66f57e6058eb5`.
Original ignored backend/frontend/scripts files were moved into
`.artifacts/legacy-local-m0-20260908/`. A Windows directory handle prevented renaming frontend;
its contents were preserved individually. No old dependencies were copied into the new project.
Other ignored `.artifacts` backups/runtimes remain in place.

At the M0 checkpoint the old `asi-verification` stack was running on ports 5173/8000/5432.
Recheck its current state before runtime operations; this observation is not a live status feed.
The new namespace is `asi-rebuild-v1`; planned ports are 5180/8010/5440 and planned volumes must
use that namespace. No new stack, schema or volumes were created at M0. Never use old data as
disposable test data; never run `down -v` against the old project.

## Current limitations

The API/database foundation and backend lockfile now exist. Authentication, frontend, worker,
ingestion and RAG remain to implement. Development generation will use explicit mock/Codex-assisted
responses; the user requires real local embeddings and retrieval. Live provider access and paid
spending remain unavailable; API connectivity/quality gates cannot be inferred from development data.
