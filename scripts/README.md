# Repository tooling guide

| Tool | Responsibility |
| --- | --- |
| `verify_built_web.py` | Build non-root compiled-web image, migrate isolated stack, run browser suite and capture/clean temporary containers |
| `verify_database_restore.py` / `recovery_manifest.sql` / `probe_restored_application.py` | Synthetic-stack restore, table fingerprints and restored API workflow checks; [runbook](../infra/README.md#local-logical-backuprestore-drill) |
| `verify.ps1` | Start isolated stack, run backend/frontend/browser checks and retain timestamped evidence |
| `wait_http.py` | Wait for HTTP 200 from all supplied endpoints with a shared deadline |
| `check_docs.py` | Enforce the maintained documentation map, plan headings and AGENTS size |
| `check_source_sizes.py` | Enforce application file-size limits and declining legacy exceptions |
| `source-size-baseline.json` | Reviewed inventory of oversized application files |
| `tests/test_source_sizes.py` | Boundary, regression and configuration-error checks |
| `seed_complex_knowledge_base.py` | Populate a development knowledge corpus; inspect target and options before use |

Run `python -m unittest discover -s scripts/tests -v` and
`python scripts/check_source_sizes.py` from the repository root. The checker has no third-party
dependencies. Its scope is application Python/TypeScript; it does not inspect CSS or test size.
Run `python scripts/check_docs.py` for the documentation gate. It checks standard inline local
Markdown links in the control documents, seven subsystem/tooling guides and execution plans,
required plan sections, and the
under-200-line AGENTS limit. It skips fenced examples and external URLs; it does not crawl all
historical tickets, validate URL availability or resolve heading fragments/reference-style links.

`python scripts/verify_built_web.py` requires the existing `asi-verification` stack and installed
frontend/Playwright dependencies. It binds a temporary image instance to loopback port 8001
(`--port` overrides), supplies a generated test signing key and mock providers, applies migrations
explicitly and runs all browser tests at one origin. CI uses `--project asi-ci`. Results/logs live
under `.artifacts/built-web-<id>/`; only generated container names are removed, never stack volumes.
The local full runner and CI browser job invoke it. Runtime/root/Node checks and cleanup
behavior have tooling regressions. Consult the [quality score](../docs/QUALITY_SCORE.md) for
current acceptance and [testing evidence](../docs/testing.md) for dated runs; a successful older
image verification does not cover subsequent application changes.

On Windows with Docker Desktop, Python 3.12+, Node/npm and PowerShell available, run `./scripts/verify.ps1`
from the repository root. It rebuilds the verification images, uses synthetic browser data,
clears model credentials and explicitly selects mock embeddings, restoring caller settings afterward.
It writes logs plus per-command exit codes/durations
under `.artifacts/<timestamp>/`. A failing check returns a nonzero exit. It leaves the stack
available for inspection. Do not use it against production data or change its project name
to a user stack. API/frontend ports are currently 8000/5173 and must be free for this project.
Pass `-PythonExecutable /absolute/path/to/python.exe` if `python` is unavailable on PATH.
The runner tests tooling and source-size policy, records readiness failures, and skips browser
execution if the application did not become ready. Other independent checks still run.
Backend lint runs before tests using `ruff check .`, matching CI and covering migrations as well
as application/tests. Resolve its concrete diagnostics before repeating expensive checks.
Runtime logs are retained in the artifact directory without being replayed into console output;
inspect them for HTTP errors and correlate request IDs before accepting the run.

## Adding tooling
`python scripts/check_http_log_privacy.py --project asi-verification` requires the running
isolated API on loopback port 8000 and Docker Compose. It sends synthetic path/query markers,
then verifies a correlated 404 outcome exists without raw markers in the server log window.
No customer data or database mutation is needed. A missing/duplicate outcome or raw access log
fails the check. This is an access-log boundary check, not complete traceback/PII sanitization.
It runs in the local verification pipeline and browser CI; hosted CI execution remains unverified.


Keep scripts deterministic with explicit inputs, bounded output, nonzero failure exits and
actionable messages. Separate command execution from policy checks and report generation.
Log command outcomes under `.artifacts/`; never silently continue after a required check fails.
Test failure paths without modifying production data or making paid provider calls.

CI lives in [.github/workflows/ci.yml](../.github/workflows/ci.yml). The new source-size job
runs locally proven checks but still needs required-check configuration on GitHub.
The browser job builds a fresh Compose stack, waits for HTTP readiness, and runs Chromium
journeys against PostgreSQL. It retains evidence for seven days and removes the disposable
CI volumes. Remote execution and required-check configuration remain unverified locally.
Dedicated PostgreSQL concurrency and migration-upgrade coverage remain in [testing](../docs/testing.md).
