# Local development runbook

## Automatic local demo answers

Install/start Ollama locally and run `ollama pull qwen2.5:7b`. Set these nonsecret values in
the ignored root `.env`, then run `python scripts/manage.py up`:

```dotenv
ASI_GENERATION_MODE=local_ollama
ASI_OLLAMA_MODEL=qwen2.5:7b
```

Compose connects API/worker to `http://host.docker.internal:11434`; native backend processes
default to `http://127.0.0.1:11434`. Only local HTTP hosts are accepted. No paid API is used.
New versioned ordinary runs distinguish automatic cited answers, exceptions needing admin
review, missing-support intervention and retained set-aside messages. Automatic answers are
internal machine results, not human approval or an external send. Missing support cannot be
approved or edited into an approval; clarify, reject or start a fresh linked attempt instead.
Inspect the recorded routing reason and sources before acting. Settings displays
the configured mode, not a readiness probe. Existing manual waits remain manual: cancel/retry
to create a fresh linked attempt. Frozen comparisons stay manual. Set mode `manual` and restart
to return new ordinary runs to development contributions. Keep Ollama running during the demo.
Source selection validates IDs and quotes server-held passages; it does not prove semantic
entailment. Provider outages/invalid outputs produce inspectable failures, not canned answers.

## Documentation maintenance

Run `python scripts/docs_freshness.py garden` for source-to-document review material,
`python scripts/docs_freshness.py generate` to regenerate factual references, and
`python scripts/docs_freshness.py check` to check generated facts and review fingerprints.
Use `acknowledge --help` only after independent review under the
[freshness protocol](DOC_FRESHNESS.md). These stdlib commands neither start services nor call AI.
The [generated source reference](generated/source-reference.md) lists current dispatcher and npm
commands directly from source; the recipes below explain their purpose and operating limits.

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
waits for API/worker shutdown (30-second container stop bound), then applies migrations and
explicitly initializes the supported PostgreSQL LangGraph checkpointer,
then starts and waits for the API, frontend and worker as well.
The frontend image contains its source: host edits/builds alone do not update the served
container. Run `up` to rebuild before collecting browser evidence for changed UI code.
Health endpoints: `http://127.0.0.1:8010/api/health/live` and `/api/health/ready`.
Readiness requires database access, current Alembic revision and pgvector extension.
`python scripts/manage.py migrate` builds the current API image and completes API/worker shutdown
before applying migrations. It leaves both stopped; run `up` afterward. Migration/checkpoint
failure also leaves writers stopped for repair, without removing volumes or restarting an old image.
Both migration paths use one-off containers with `--no-deps` after database readiness. A build
failure occurs before shutdown. This prevents old application writers inserting rows after backfill.
`down` preserves volumes.

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
Synthetic user provisioning and browser login exist; follow the development sign-in section.
Credentials are generated by `seed-demo`, not a shared default admin password.

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
TXT/Markdown ingestion, real retrieval and the connected message-to-cited-draft workbench exist;
human-review verification is in progress. Development generation uses explicitly attributed Codex-assisted
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

### Development generation comparison CLI

From `backend`, run `uv run --frozen python ../evals/generation_cli.py ACTION
--credentials ../.artifacts/m1/demo-credentials.json --workspace UUID --output NEW_JSON_PATH`.
The CLI targets local development8010/Origin5180 and authenticates as the seeded administrator.
Use `--session ../.artifacts/m5/generation-session.json` across commands to reuse a server-validated
session and avoid repeated logins. This file contains a session credential: keep it local and
ignored like demo-credentials.json; the CLI rejects paths outside repository .artifacts.
`create` additionally needs `--input QUESTION_JSON --key STABLE_KEY`; the JSON contains only
`original` and `language` (en/ja/zh). Save the returned comparison ID. `read` and `cancel` need
`--comparison UUID`. `export` and `submit` also require `--pipeline NAME`; submit reads
`--input RESPONSE_JSON` containing the exported context_hash/request_hash, answer and citations.
Use direct_llm/vector_rag/hybrid_rag/system_v1. Only direct permits empty citations. Export
returns one pipeline's rendered request; do not include rubrics or other answers in generation.
Poll `read` using new output filenames while workers prepare requests. System responses resume
the actual support run and need the ordinary Workbench review. `list` returns a bounded page.
Existing output files are never overwritten. Corpus changes require a new comparison; completed
history remains inspectable. This is attributed development work, not a live model quality test.

Administrators can also open Quality → Generation comparisons to create, inspect and cancel a
comparison. Expand retrieval evidence or open the governed workflow for review; original answers
and reviewed wording are separate. Request export/contribution still uses the CLI above.
With the development stack and seeded accounts available, run `npx playwright test
tests/e2e/comparisons.spec.ts` from frontend using the browser/evidence environment above.
This dedicated test covers create/inspect/cancel, desktop/mobile layout and injected history
denial; actual membership revocation is covered by PostgreSQL integration tests. It is separate
from the baseline `test:app` command and does not measure semantic quality.

### Frozen generation batch

From the repository root, run `uv run --project backend --frozen python evals/run_generation.py
prepare --directory .artifacts/m5/NEW_BATCH` with the development runtime/model and seeded users
ready. This creates new isolated evaluation workspaces, ingests the frozen corpus and admits30
cases. Run the same command with `collect` and the same directory to refresh all four outcomes
and save available requests under `requests/CASE/PIPELINE.json`. Use one process per directory.
The ignored report stores comparison IDs and stable admission keys; never edit them to bypass
the frozen-input checks. Failed ingestion requires a new directory; collection/admission failures
can resume with existing keys. Original failed evidence is retained.
Use the single-case CLI above for attributed contributions, then collect again. Zero exit status
means snapshot collection succeeded, including unfinished cases, not that answers passed quality.
Full response/review collection and external-provider verification remain incomplete.

### Generation review scoring

From the repository root, run `uv run --project backend --frozen python evals/score_generation.py
--directory .artifacts/m5/BATCH --judgments .artifacts/m5/JUDGMENTS.json
--output .artifacts/m5/NEW_SCORE.json`. The output must be new. An empty JSON array of judgments
produces all120 observation hashes with no reviewed successes; it does not generate answers.
Review one original response at a time against its request, active source versions and frozen
case facts. Keep these evaluator inputs away from response generation. A judgment has case_id,
pipeline, observation_hash from the score output, reviewer, kind (human or codex_assisted),
rationale (at least20 characters) and checks. checks contains exactly the five boolean keys
from evals/generation-review-v1.json. Explain source support and uncertainty in the rationale;
do not assert entailment merely because quotes match. Use a reviewer separate from the response
author where possible and record attribution honestly. Names are assertions, not authentication.
Recollect after contributions, then generate fresh bindings. Edited system replies are excluded
from original-response scoring. A changed observation invalidates its old judgment. Exit0 means
the score report was produced; inspect development_target_met and per-language denominators.
No local review result establishes external-provider quality, inference latency or billing.

Development uses Vite's same-origin API proxy; frontend container file ownership permits
temporary config/cache writes by its non-root user. No external font service is required.
Built release serving has separate setup and evidence below; remaining release gates are incomplete.

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

The current ingestion API accepts UTF-8 TXT/Markdown up to 5 MiB. PDF/DOC extraction is deferred beyond V1.
Admins upload/replace/withdraw; all workspace members may list and preview sources. Uploads
require an idempotency key. Replacements become active only after successful indexing; failed
replacements preserve the old active version. Limits: 500 active documents, 20 versions per
document, 500 MiB retained originals, 50,000 retained chunks per workspace, 1,000 per document.
Splitting checks cancellation between bounded 8,000-character blocks and preserves section and
normalized Unicode character offsets. A position-carrying adapter retains the actual occurrence
in repetitive text while reusing LangChain merging; dependency upgrades require compatibility
tests. The final recorded chunk is re-split with the next work block;
real headings reset overlap, and sentence separators remain with preceding text. Existing
chunks require normal versioned re-ingestion to receive these repairs. Opaque ASCII tokens
longer than 4,096 characters fail.
Original bytes and checksum remain available separately from normalized text.

Migration 0010 adds lexical frequencies, length and recipe without replacing stored chunks,
vectors or citations. It reads at most 500 rows per batch in the migration transaction and
backfills every retained chunk; failure rolls the transaction back. This is a local maintenance
operation, not an online backfill service. New ORM inserts derive metadata from immutable text.
The default search uses vector/reranker; explicit BM25/hybrid strategies reject incomplete active metadata,
including SQL NULL, JSON null and unsupported recipe versions. See [RAG design](RAG.md).

Migration0011 adds `retrieval_traces.stages`; historical traces keep an empty object, not
reconstructed candidate history. POST retrieval accepts `strategy`: `vector`, `bm25`, `hybrid`,
`vector_rerank` (default), `hybrid_rerank`. GET the same path plus `/{trace_id}` returns
permission-gated candidate history (maximum40). BM25-only records no model call. Knowledge
search has an optional Search method selector; workflow defaults are unchanged. Expand Retrieval
evidence to inspect ranks and exact sources. Missing branch scores are not zero confidence.

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
recovery. Support integration tests additionally exercise the application graph and authorization,
including concurrent submissions and checkpoint-before-publication lease loss. This simulates
the failure boundary; operating-system process-kill recovery is still unverified.

## Development message-to-draft API

`up` runs `python -m app.workflows.checkpoints` in the backend container after Alembic migrations.
This explicitly creates/upgrades supported checkpointer tables; never expose raw checkpoint reads
or arbitrary resume commands to clients.

Under `/api/workspaces/{workspace_id}`, an operator/admin posts `/messages` with an
`Idempotency-Key` and JSON `{original, language}` (`en`, `ja` or `zh`, up to 1,000 characters).
All members can read paginated `/messages` and `/runs/{run_id}`. Poll the latter for state,
original input, draft, exact citations, graph steps and model records.

When state is `waiting_for_input`, an admin exports `/runs/{run_id}/development-handoff`.
The export includes generation_request, request_hash and request_storage (`recorded` for new
handoffs, `reconstructed` for older rows). Read its actual bounded context and author an answer
from those sources. Updated clients include request_hash; legacy clients may omit it and retain
the existing context_hash binding. The server verifies stored request identity in either case. Submit to
`/runs/{run_id}/development-handoff/{handoff_id}` with its `context_hash`, `answer` and
`citations: [{chunk_id, quote}]`, using exact nonempty source quotes. Normal session, CSRF and
Origin requirements apply. Include `review_category` (`ordinary`, `policy_exception` or
`conflicting_evidence`); the default for new submissions is ordinary. Submission schedules
continuation; poll until `awaiting_review` or failure. Legacy contributions without this field
remain unclassified and require administrator approval.
The original requester must retain operator/admin access. Source withdrawal/replacement,
cancellation or revoked authority blocks publication. Identical submissions are safe to repeat;
different submissions return conflict. Operator/admin cancellation uses `/runs/{run_id}/cancel`.

These are development contributions with contributor identity and handoff elapsed time, not
OpenAI API calls or inference latency. Exact citations prove source provenance, not semantic
support. Drafts remain unverified until an authorized review; exact citations alone do not prove
semantic support. Reversed raw timestamps show `timing_status: clock_anomaly` and null elapsed.

POST `/runs/{run_id}/review` with `action` (`approve`, `edit`, `reject`, `clarify`), a nonempty `reason`,
the current `expected_revision` and `draft_hash`. Edit requires replacement `response`; clarify
requires a question in `response` (maximum 1,000 characters). Approve/reject omit response.
Published clarification has outcome `clarification_needed` and no approved response. Operators/admins
may review ordinary drafts; approving/editing policy exceptions or unclassified drafts requires
admin. Submission returns 202 and schedules continuation. Poll state/outcome until completed,
rejected or failed; approval records a response internally and does not send it to a customer.
Same actor/payload retries are idempotent; conflicting decisions return 409. Original drafts,
citations and decision history survive cancellation/publication failure.

## Workbench demo and verification

Use **Message view** to focus on Needs attention, Ready responses, Processing or Failed.
Search combines with the selected view; **Clear filters** restores all messages. Results reflect
the latest attempt, and the selected detail stays open even when it leaves that view. The
server accepts the corresponding `view=all|attention|ready|processing|failed` query on the
workspace messages endpoint. Unknown views return 422; membership remains server-enforced.

After runtime/model preparation, open `http://127.0.0.1:5180` and sign in with the seeded admin.
Select **New message**, enter a customer question and response language, then **Start processing**.
The selected message shows progress. For an evidence-backed question, open **Development response
controls**, choose a retrieved passage, supply an exact quote and a response grounded in that
evidence, then **Submit development draft**. The worker resumes and persists the draft.
In **Review response**, choose approve/edit/reject and give a reason. After completion, the
approved response is primary; expand the preserved original draft and review decision as needed.
To ask for missing information, choose **Request clarification**, enter **Question for the
customer** and a reason, then **Record clarification request**. After processing, the question
is primary and the unapproved draft stays collapsed. Record the customer's reply through
**Add customer details**; it starts fresh retrieval. This action does not send a customer message.
Select a numbered citation to inspect its saved excerpt, then open the exact document version.
Expand **Processing details** for graph steps, model identity, timings, tokens and external charges.
Use **Cancel processing** while a run is queued, processing or waiting; cancellation is a server
operation, not browser navigation. A single `w` asks for clarification without invoking a model.
Open **Add customer details** to provide meaningful input and start a linked attempt with fresh
retrieval. Failed/cancelled/rejected attempts and insufficient-evidence outcomes offer **Retry
processing**. Expand **Attempt history** to inspect earlier inputs/results, or use **Open latest
attempt** to return. The original message stays unchanged; inputs are capped at 1,000 combined
characters and messages at ten attempts. Active processing must be cancelled before retrying.

With indexed synthetic refund-policy smoke knowledge present, run
`npx playwright test tests/e2e/workbench.spec.ts` from `frontend` using the browser/evidence
environment variables described above. The suite uses actual local retrieval and deterministic
development contributions, plus explicit network-failure injection. It covers EN/JA/ZH drafts,
sources, approve/edit/reject, cancellation, viewer access, 360/768/1440px, keyboard focus and doubled content size.
The linked-attempt journey also checks clarification, cancellation/retry and preserved history.
This is not a browser-native zoom or live generation-quality measurement. Baseline `test:app`
also exercises a persisted clarification flow without prepared models, including in CI.

For the built release, set ASI_APP_BASE_URL to http://127.0.0.1:8011 and ASI_DEMO_CREDENTIALS
to ../.artifacts/m6/release-credentials.json in the frontend shell. The same workbench.spec.ts
and workflow-inspector.spec.ts use those overrides; development remains the default. Prepare
the real local models and index the long synthetic customer handbook first. Exact quote checks
preserve original whitespace; fact checks allow policy line wrapping.
Repeated suites reuse seeded accounts and may reach the unchanged ten-logins-per15-minute
account limit, including successful logins. Retain429 evidence and wait for the normal window
expiry before a focused rerun; do not reset counters or weaken authentication to clear a test.
Use separate browser contexts and never publish raw login snapshots or credential files.
The same release overrides also apply to app.spec.ts, settings-usage.spec.ts,
message-import.spec.ts and inbox-views.spec.ts. These reuse the existing session/admin/import
journeys against built assets. The settings harness restores the captured original language on
success or failure; cleanup failures remain visible alongside the original error. Run these only
against the isolated synthetic demo workspace, not concurrently with a human editing its defaults.
The arbitrary unavailable-workspace URL in app.spec.ts is UI recovery evidence; use the separate
real private-workspace release smoke and PostgreSQL matrix for actual tenant-isolation claims.

## Retrieval recovery checks

`python scripts/manage.py verify-integration` allows a bounded 420 seconds for the expanded
PostgreSQL suite, including actual child-process termination and database-session loss. This
command timeout is separate from application latency acceptance gates.

The integration helpers wait only when a fresh, unattempted job of the intended workspace/kind
has an observed future availability time. Waiting is bounded by five monotonic seconds, closes
each observation transaction and never changes timestamps or retries worker execution. Local
evidence records these waits in `job-readiness.jsonl`. This handles observed database-clock
regression in synchronous test setup; it does not fix the host clock or bypass retry backoff.

For the initial ownership-protocol transition, stop old producers from the repository root:
`docker compose --env-file .env -f compose.yaml -p asi-rebuild-v1 stop api worker`, then run
`python scripts/manage.py up`. This keeps existing volumes and prevents old inference from
overlapping the new sweep. Do not run an older API or worker alongside this version: old
inference lacks the lock protocol. The worker automatically reconciles bounded batches; `retrieval_ownership_recovered`
logs only a repaired count. Inspect protected run/model details for `uncertain` and
`retrieval_ownership_lost`; unknown usage/cost remains unknown. Retry processing creates a fresh
attempt. Never clear these records or fabricate finished accounting to make the display green.

## Inbox capacity verification

Run `python scripts/manage.py verify-inbox-capacity` after the local rebuild database is running,
backend dependencies are synced, frontend dependencies are installed and the project-local
Playwright browser is available. Node.js is required. The command creates disposable migrated
schemas only in `asi_rebuild_test`; it never loads the application or archived data with fixtures.

It inserts 50,000 synthetic primary messages plus 100 foreign messages and newer attempts,
checks actual API counts/order/ACL/page limits, and starts temporary loopback Uvicorn/Vite
processes for a real browser journey. No route responses or database queries are mocked; no
provider calls or worker processing occur. A separate fixture verifies concurrent 49,999→50,000
admission and idempotent replay. All temporary process trees are stopped before schema teardown.

Evidence under `.artifacts/m0/inbox-capacity-<timestamp>/` includes command/source fingerprint,
`inbox-capacity.json` (measurements and EXPLAIN ANALYZE/BUFFERS), browser JSON/screenshots/traces
and server/launcher logs. Saved credentials are fixed synthetic test accounts. The local benchmark
requires per-case warm p95 <=1,000ms: six observations, first excluded, five warm samples, so
that percentile is effectively the observed maximum. This is a small local sample, not an SLO.
The ordinary integration suite checks capacity correctness without a hardware-sensitive timing
assertion or browser startup. Both wrappers have a 420-second process timeout for the enlarged
fixtures; that timeout is distinct from the 1,000ms request budget. Fresh workspace-owned pytest
temporary directories avoid shared Windows temp ownership failures. Browser logs stream before
waiting, and a real child-process timeout regression checks cleanup and retained diagnostics.
Normal completion and inner browser-timeout cleanup own the process trees. Forced external
termination of the entire verification wrapper is not covered by that cleanup test.

For an explicit five-strategy comparison, run `uv run --project backend --frozen python
evals/compare_retrieval.py` from the repository root. Keep source files unchanged while it runs.
Exit0 means the experiment completed consistently; inspect individual retrieval gates and paired
regressions. It never changes the default. See [evaluation](../evals/README.md) for the protocol.


## Import customer messages

Workbench → Import accepts a UTF-8 `.jsonl` file (optional UTF-8 BOM), at most1 MiB and100
nonblank newline-delimited records. Each original is1–1000 characters; language is en/ja/zh.
Example (one JSON object per line):

```jsonl
{"original":"What is the refund deadline?","language":"en","labels":["billing"]}
{"original":"返金期限はいつですか？","language":"ja","labels":["返金"]}
```

Labels are optional: at most10, each1–32 characters after trimming/casefolding; letters, numbers,
spaces, hyphens and underscores only. Duplicates are removed. Invalid UTF-8 rejects the file with an encoding error.
Unknown/duplicate JSON fields and invalid rows reject the entire batch with a line number,
without echoing customer text. One invalid row or insufficient quota creates no messages/jobs.

Operators/admins import, edit labels and start processing; viewers inspect. Import saves customer
data only: it queues no AI jobs and adds no trusted knowledge. Open Not processed, filter by
label/text, inspect a message, then Start processing. Existing labels/originals remain available
through the inbox's Labels & original link after processing. Only the selected message starts.

API: multipart `POST /api/workspaces/{id}/message-imports` with file and Idempotency-Key; replay
of identical actor/filename/bytes returns the same batch. `GET /messages/{message_id}`,
`PUT /messages/{message_id}/labels`, and `POST /messages/{message_id}/process` share that workspace
prefix. Concurrent process calls converge on the same initial run. The existing50000-message
workspace quota counts unprocessed rows too. The UI preserves the import key for retries while
the same form/file remains open; selecting a file again is a new import, not content deduplication.


## Settings and usage

Settings → Processing defaults lets an admin preselect en/ja/zh for new manual messages.
Existing messages and JSONL imports retain their own explicit language. Settings also links
member management and shows configured local model identities/revisions, alongside the explicit
configured manual/local generation mode. This display does not probe provider readiness.
`GET/PUT /api/workspaces/{id}/settings` is admin-only; PUT accepts default_language only.

Quality → Model usage shows the current workspace's last1,7,30 or90 days.
`GET /api/workspaces/{id}/usage?days=7` accepts1–90 days for any workspace member. Known sums
exclude missing measurements; missing counts remain visible. External charge is ledger-recorded,
not verified billing or total operating cost. Started/uncertain records remain distinct from
success/failure. At most20 groups are shown; aggregate totals include all groups. Quality also
exposes registered historical retrieval reports through the command described below; neither
view certifies generated-answer correctness.


## Standalone development database backup

`python scripts/manage.py backup` exports the isolated **development** database in
`asi-rebuild-v1-postgres-1`, using the connection configured by `.env`. It does not select the
packaged release database or archived stack. It validates the container identity, exports a
read-only PostgreSQL snapshot, fingerprints its public tables and writes a custom-format
`snapshot.dump` plus `report.json` under `.artifacts/m6/backup-<timestamp>/`.
The report includes the archive byte count and SHA-256; a failed or empty export exits nonzero.
Partial archives and failed reports remain for diagnosis and must not be treated as backups.

This command creates no database and runs no restore, login, worker or model operation.
`status: passed` means export succeeded; `restoration_verified: false` remains explicit.
Sequence values are observational metadata, not transactionally frozen sequence state.
Backups contain application data, documents and authentication records. Keep them protected;
they are ignored by Git. They exclude `.env`, model caches and machine configuration.
This command does not implement encryption, off-device retention or a recovery-time objective.
Use the drill below for a fresh snapshot, or its saved-backup option to consume this archive.

### Verify a trusted saved backup

Run `python scripts/manage.py verify-restore --backup-dir .artifacts/m6/backup-<timestamp>`
with an actual backup directory from the command above. Only direct `backup-YYYYMMDDTHHMMSSZ`
directories under this checkout's `.artifacts/m6` are accepted. The directory, manifest and
archive must resolve within that boundary. Manifests are bounded to2 MiB and archives to512 MiB.
Only successful standalone development backup manifests are accepted.

The command copies and verifies the archive into a new `restore-saved-<timestamp>` evidence
directory before creating a random disposable database. It compares restored rows/metadata to
the saved manifest, then exercises a new request in the clone. It does not dump or compare
against today's source data. Original backups and existing databases remain unchanged; failures
retain evidence and any newly created clone. It does not switch the app's connection or migrate
an older schema to current code; incompatible archives fail rather than being silently upgraded.

Use only trusted operator-created backups. A checksum detects corruption relative to its
manifest, not malicious replacement of both. PostgreSQL restore executes the archive's SQL;
see the [PostgreSQL restore guidance](https://www.postgresql.org/docs/current/app-pgrestore.html).
This is a local operator command, not an archive-upload endpoint or general disaster-recovery SLA.

## Fresh snapshot restoration drill

`python scripts/manage.py verify-restore` is a local verification operation. It validates the
rebuild PostgreSQL container, captures a read-only exported snapshot and dumps that same snapshot
under `.artifacts/m6/restore-<timestamp>/`. It creates a new random `asi_restore_<hex>` database;
there is no existing-target overwrite or database-drop operation. Original app/archive databases
and existing Compose API/worker connections remain unchanged.

The drill compares every public table's row count and SHA-256 of ordered JSON rows (UTC), plus
extension versions and sequence values, before any clone login. Only after parity does it cancel
inherited active jobs in the disposable clone and create a separate synthetic account/workspace.
ASGI TestClient and the real worker/LangGraph process a new ambiguous message to clarification,
checking job success and persisted checkpoints without model calls. It retains the dump, manifest
and disposable database for review. Dumps contain application data and stay local/ignored.
This is a fresh-backup/API-worker proof, not an old-backup recovery point, network-server/browser
restore check, safe replay of inherited jobs or restored RAG/generation quality claim.

## Copy an approved response

Open a completed approved result and select **Copy approved response**. It copies the final
approved wording, including edits and line breaks, without adding the original draft or citations.
The success message confirms the browser clipboard operation, not delivery to a customer.
If clipboard access fails, select the visible response text manually or retry. All workspace
members who can inspect an approved response can copy it; the action does not modify data.

## Built local release

From the repository root, run in order:

```text
python scripts/manage.py release-up
python scripts/manage.py release-seed
python scripts/manage.py release-prepare-model
```

Open `http://127.0.0.1:8011`. This separate `asi-release-v1` stack contains API, worker and
PostgreSQL; FastAPI serves the built UI without Node/Vite in the runtime image. Its port and
trusted origins are explicitly fixed to localhost/127.0.0.1:8011 in infra/compose.release.yaml.
The shell is public; protected data still requires login and workspace authorization. Invalid
API paths, missing assets, private filenames and unsupported SPA routes do not return HTML.

release-up generates `.artifacts/m6/release.env` once, builds the image, stops existing release
writers, migrates, initializes checkpoints and starts healthy release services. Any failed step
stops the sequence; migration failure leaves writers stopped. release-seed creates separate
synthetic credentials at `.artifacts/m6/release-credentials.json`; never use it on customer data.
release-prepare-model downloads the pinned existing CPU embedding/reranking models to the
release-only model volume and verifies actual inference. Run it before uploading knowledge;
startup health alone does not prove cached models exist. No paid generation is enabled.

Use a separate browser profile/context for development versus release: cookies for the same
hostname are shared across ports. `python scripts/manage.py release-down` stops only the release
project and preserves its volumes. The development/archive stack remains untouched. Do not use
Compose volume deletion for routine restart. Commands retain logs/fingerprints under
`.artifacts/m0/release-*`; outer forced-termination cleanup is not proven by successful runs.

After release setup, run `npx playwright test tests/e2e/release.spec.ts` in frontend with the
normal browser/evidence environment variables. For the existing knowledge journeys, additionally
set `ASI_APP_BASE_URL=http://127.0.0.1:8011` and
`ASI_DEMO_CREDENTIALS=../.artifacts/m6/release-credentials.json`, then run
`npx playwright test tests/e2e/knowledge.spec.ts`. These tests use isolated browser contexts.

Backend unit verification now allocates a unique ignored `.artifacts/pytest/<uuid>` base to
avoid shared Windows pytest-temp ownership failures. Process-kill retrieval tests retain phase,
exit-status and scoped trace/ledger-state diagnostics, plus a bounded stack dump on slow startup.
Their 20-second dispatch deadline and recovery assertions are unchanged.

The OpenAPI generation tool currently needs a scoped npm override: @redocly/openapi-core pins
an affected js-yaml version, so frontend/package.json selects js-yaml4.3.2 for that parent.
This addresses GHSA-2883-xcg3-v3hh without a broad toolchain upgrade. Reassess the override when
upgrading Redocly/openapi-typescript; require a clean audit and unchanged generated API types
(or a separately explained schema change) before removing it.

## Register historical retrieval results

`uv run --frozen python -m app.register_evaluation REPORT.json --actor-id ADMIN_UUID`
runs from backend with ASI_DATABASE_URL configured through the normal secret environment.
This local administrator command registers existing evidence; it does not run AI or evaluations.
For the isolated development container, copy the synthetic report to a temporary container path,
then run the same module with `docker exec asi-rebuild-v1-api-1 uv run --frozen python -m
app.register_evaluation /tmp/REPORT.json --actor-id ADMIN_UUID`. Resolve the actual seeded actor ID;
never pass database passwords on the command line. Require migration0014 first through normal `up`.

The command accepts at most8 MiB and only completed valid v1 five-strategy comparisons with
30 cases per strategy and two negative probes. It rejects inconsistent outcomes and missing,
foreign or mismatched trace references. The actor must administer the report's actual primary
workspace. It never aliases evidence into a different workspace. Identical raw bytes are
idempotent; changed bytes are a separate historical record. Raw foreign probe metadata and
local file maps are discarded from the stored projection. An accepted hash establishes identity,
not independent truth. The raw report remains a protected local artifact.

In that workspace open Quality → Retrieval checks. Compare strategies, filter failed/excluded
cases and languages, then open Retrieval evidence for stored traces. Provenance distinguishes
registration time from the report's unknown execution timestamp. Other workspaces show their
own history or an empty state. Generation evaluation remains unverified.
Run `npx playwright test tests/e2e/evaluations.spec.ts` after registering the existing real
`.artifacts/m2/strategy-comparison-20260909T083207Z/report.json`; ASI_EVALUATION_REPORT can select
another compatible registered report. The browser test uses the existing synthetic demo users.

## Five-session release profile

After isolated release setup and model preparation, run
`npx playwright test tests/e2e/small-team.spec.ts` from frontend with PLAYWRIGHT_BROWSERS_PATH
and ASI_EVIDENCE_DIR set as above. It uses release-credentials.json, adds two synthetic long
policies, opens five separate sessions of the seeded operator, and concurrently admits EN/JA/ZH
requests with background ingestion. Each operator inspects real retrieval/model records and
cancels at the development handoff. It does not exercise generation or five distinct accounts.
Artifacts retain incremental outcomes on failure; failed runs may leave admitted work for inspection.
Repeated runs preserve existing data and add synthetic records; this is not a pristine-corpus benchmark.

Read the resulting profile.json for workspace/run/document IDs. Inside the release container run
`uv run --frozen python -m app.profile_release --workspace-id UUID --run-ids R1 R2 R3 R4 R5
--document-ids INITIAL_DOCUMENT BACKGROUND_DOCUMENT` using `docker exec asi-release-v1-api-1`.
This trusted local database command takes a read-only repeatable snapshot, scopes all records to
the workspace and refuses partial/missing sets. It is not an HTTP endpoint or member authorization API.
The second document identifies the background workload. Save its JSON alongside the browser report.
Compare recorded admission-to-indexed and admission-to-handoff intervals to establish overlap;
both include queued work and do not prove simultaneous inference. Admission-to-first-node also
includes pre-node work. Null means unmeasured; negative values remain clock anomalies.
Current corpus counts describe collection time, not an inferred historical snapshot.
Inspect bounded worker/API logs and screenshots before drawing conclusions. See the
[recorded profile](plans/completed/m6-small-team-profile.md) for sample timings and limits.

The Verify workflow also runs release.spec.ts in a separate Ubuntu release-smoke job. Each job
builds fresh packaged assets, migrates/checkpoints and seeds disposable CI identities, then checks
same-origin assets, worker clarification, nested refresh, CSRF/logout and workspace/viewer denial.
It uses the existing release commands and always attempts to stop its isolated stack; it never downloads
inference weights or calls generation providers. Failed runs print bounded service logs before
cleanup. Job cancellation or timeout can interrupt cleanup; browser files currently remain on the
ephemeral runner rather than being uploaded. This is a packaged no-API smoke, not the real-model
five-session or full release matrix.


Command evidence uses file-backed stdout/stderr capture and bounded process waits. On timeout,
the wrapper terminates the launched Windows process tree or POSIX process group before reporting
exit124 and retained partial output. It does not target unrelated services. Cleanup uncertainty is
explicit in command.log; deliberately detached processes are outside the tree guarantee. Timeout
is a failed command, never a passing test result. Runtime commands keep their existing budgets.
