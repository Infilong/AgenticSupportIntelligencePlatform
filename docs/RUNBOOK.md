# M0 preparation runbook

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

No runtime `.env`, live provider access, API spending budget, backend dependency lockfile,
application startup, authentication, ingestion or RAG exists yet. `.env.example` lists proposed
settings only. M1 must replace proposals with implemented configuration and tested commands.
M2 must obtain live access/spend authority and verify model/embedding compatibility.
