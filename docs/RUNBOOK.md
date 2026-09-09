# Local development runbook

## Development stack

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
files are preserved. `up` starts the fixed `asi-rebuild-v1` database, builds the API and frontend,
applies migrations, then starts and waits for the API, frontend and worker as well.
The frontend image contains its source: host edits/builds alone do not update the served
container. Run `up` to rebuild before collecting browser evidence for changed UI code.
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

API/database, authentication, frontend and worker foundation now exist.
TXT/Markdown ingestion and real retrieval exist; application generation/workflow remains unfinished.
Development generation will use explicit mock/Codex-assisted
responses; the user requires real local embeddings and retrieval. Live provider access and paid
spending remain unavailable; API connectivity/quality gates cannot be inferred from development data.

## Development sign-in and frontend verification

Run `python scripts/manage.py up`, then `python scripts/manage.py seed-demo`.
Open `http://127.0.0.1:5180`. Generated synthetic account credentials are kept in ignored
`.artifacts/m1/demo-credentials.json`; do not commit them. Seeding is explicit and limited to
the rebuild database. Repeated seeding preserves existing passwords, changed roles and removed
memberships. Lost credentials are an error; the command never resets an existing account.

From `frontend`, run `npm ci`, `npm run build`, `npm test`, and `npm run test:app`.
Application tests require the running stack, seeded accounts and installed Playwright Chromium;
the older `test:environment` remains only a synthetic browser probe. On this Windows machine,
set `PLAYWRIGHT_BROWSERS_PATH` to the repository `.artifacts/browsers` before browser tests.
Set `ASI_EVIDENCE_DIR` to a new ignored output directory for each retained browser run.
Application tests exercise real API/database flows; explicit outage and revocation response
injection verifies UI recovery, while server expiry/revocation is tested against PostgreSQL.

To regenerate the frontend API contract, run `uv run --frozen python -m app.export_schema`
from `backend`, redirect UTF-8 output to `.artifacts/openapi.json`, then run
`npm run generate:api` from `frontend`. This does not connect to a database.
The generated declaration is a size exception; API owners change response schemas and regenerate.

Development uses Vite's same-origin API proxy; frontend container file ownership permits
temporary config/cache writes by its non-root user. No external font service is required.
Release static-asset serving and the remaining product journeys are not complete.

## Worker verification

`python scripts/manage.py up` starts all four development services, including the worker.
After `seed-demo`, run `python scripts/manage.py verify-worker`: it enqueues a real database
diagnostic and waits for the separate worker to persist its result. Reports include the job ID
for correlation with `docker compose -p asi-rebuild-v1 logs worker`; raw payloads are not logged.
The worker health check requires a recent successful database poll/lease renewal, not just a PID.
`verify-integration` covers atomic claims, idempotency, rollback, retries, cancellation, expired
leases, stale writer rejection and actor revocation while a handler is running.

## Real local embedding preparation

The pinned multilingual-e5-small model runs on CPU, with 384-dimensional normalized vectors.
Dependencies are locked; Linux/Windows PyTorch comes from the explicit official CPU index.
After rebuilding with `up`, run `python scripts/manage.py prepare-model` to download the pinned
public weights into the isolated persistent `embedding_models` volume and run actual EN/JA/ZH
inference. No provider key or paid API is needed. The initial download is separate from query
latency. The command allows ten minutes and preserves partial output on timeout.

Application embeddings default to local-files-only loading and fail if weights are missing.
To check offline inference explicitly, run `python -m app.providers.prepare_model --offline`
inside the backend environment with `ASI_EMBEDDING_CACHE` pointing to prepared weights.
The local Windows cache used for verification is ignored `.artifacts/models`; Docker has its
own cache volume. Each input includes the model-required query/passage prefix. Inputs above
512 model tokens are rejected instead of silently truncated; batches are limited to 16.
This inference smoke test does not prove document retrieval or answer quality.

## Knowledge ingestion

After `up`, `seed-demo` and `prepare-model`, run `python scripts/manage.py verify-ingestion`.
It signs in with ignored synthetic credentials, submits a fresh policy through the API, waits
for the real worker/CPU model, checks activation and downloads the exact original. It creates
a new smoke document on each run; it is not the long-corpus quality gate.

The current ingestion API accepts UTF-8 TXT/Markdown up to 5 MiB. PDF/DOC extraction is pending.
Admins upload/replace/withdraw; all workspace members may list and preview sources. Uploads
require an idempotency key. Replacements become active only after successful indexing; failed
replacements preserve the old active version. Limits: 500 active documents, 20 versions per
document, 500 MiB retained originals, 50,000 retained chunks per workspace, 1,000 per document.
Splitting checks cancellation between bounded 8,000-character blocks and preserves section and
normalized Unicode character offsets. Opaque ASCII tokens longer than 4,096 characters fail.
Original bytes and checksum remain available separately from normalized text.

## Real retrieval smoke

After indexing the policy, run `uv run --frozen python -m app.retrieval_probe` from `backend`.
The authenticated API embeds the query locally, searches actual PostgreSQL vectors and returns
exact passages. The probe checks the standard refund rule and resolves every returned span.
This one-policy smoke does not replace frozen multilingual corpus evaluation.
Search returns candidates, not an asserted supported answer. Ranking retrieves the best 20
authorized PostgreSQL cosine candidates, then scores question/passage pairs with the pinned
local multilingual cross-encoder. The initial overlap-fusion baseline remains in git history;
it is not BM25. Each search records a protected workspace trace and linked embedding/reranking
attempts. Reranker input tokens are computed locally using its tokenizer, not provider billing.
Pairs are bounded to 512 model tokens; original passages and offsets remain unchanged.
Membership and current source versions are rechecked after scoring; changed sources cannot
be published under replacement identities. Queries are limited to 1,000
characters and the model's 512-token cap; at most ten passages may be returned.
`prepare-model` now prepares both pinned local models. The reranker is
`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` at
`1427fd652930e4ba29e8149678df786c240d8825`; runtime never downloads weights implicitly.

Knowledge UI is at `/w/<workspace-id>/knowledge`. Admins upload/replace/withdraw/restore;
viewers can inspect documents and search. The current file formats are TXT/Markdown only.
With the real runtime/model ready, run `npx playwright test tests/e2e/knowledge.spec.ts` from
`frontend`, with `PLAYWRIGHT_BROWSERS_PATH` set to the prepared `.artifacts/browsers` and
`ASI_EVIDENCE_DIR` to an ignored output directory. This suite uses actual CPU embeddings;
it creates a synthetic travel policy and does not run in baseline CI without model preparation.

For the full frozen retrieval corpus, run `python evals/freeze_retrieval.py`, then
`uv run --project backend --frozen python evals/run_retrieval.py` from the repository root.
Requires `up`, `seed-demo` and `prepare-model`. It verifies API/worker container source hashes,
creates new isolated synthetic evaluation workspaces, uploads/indexes all sources through the
API and runs fixed multilingual queries. It preserves reports under `.artifacts/m2/retrieval-eval-*`.
Expected facts are read only by the evaluator. The run includes real local embeddings and
PostgreSQL, not live generation; it does not authorize or require a paid API.

LangGraph persistence compatibility is included in `python scripts/manage.py verify-integration`.
`test_graph_checkpoints.py` initializes the supported checkpointer only in disposable test
schemas, closes/reopens connections and reconstructs graphs to verify interrupt and failure
recovery. This is a prerequisite test, not the support application's graph or authorization
implementation. Production checkpoint initialization and the message/handoff workflow remain
the next slice; never expose raw checkpoint reads or arbitrary resume commands to clients.
