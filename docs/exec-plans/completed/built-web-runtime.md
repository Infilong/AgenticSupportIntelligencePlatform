# Built browser runtime
## Goal
Run compiled browser assets and API at one origin without a development server.
## Context
Default Compose intentionally runs Vite dev. The browser client already supports an empty
VITE_API_BASE_URL at build time, permitting same-origin calls without source changes.
## Requirements
Optional explicit static directory, startup validation, fixed index/assets exposure, preserved
API errors/authentication, no traversal/source exposure, reproducible build, non-root runtime.
## Non-goals
TLS, production credentials, hosted CI, durable recovery or replacing the local dev profile.
## Acceptance Criteria
Static tests verify content/cache behavior, missing configuration and API boundaries. Built
image serves real EN/JA/ZH browser workflows at its API origin as a non-root user without Node/Vite.
## Plan
1. Add optional static serving using existing Starlette dependencies and boundary tests.
2. Build a root-context multi-stage deployment image with same-origin frontend assets.
3. Run a separate loopback-only verification container and browser workflows; inspect logs.
4. Document exact startup/migration requirements, evidence and remaining release limits.
## Verification
Focused backend tests/Ruff, Docker build, UID/runtime inspection and Playwright against the new
origin. Use isolated mock providers/database, retain existing verification services and volumes.
## Risks
Accidentally serving repository/secrets, shadowing API 404s, stale index caching, duplicating
runtime build configuration. Expose only index and assets; keep migration invocation explicit.
## Progress
2026-09-08: inspected runtime/client, existing dependencies and local profile boundaries.
Implemented optional static serving, root-context multi-stage image and build-context exclusions.
Ruff and 37 backend tests pass. Compiled browser/API image passes 27 browser checks in explicit
production mode; final default-production image passes four multilingual checks and missing-key
startup rejection. UID 10001, no Node/npm, migration 0030 and clean runtime outcomes verified.
Temporary probe container removed. [Exact evidence](../../testing.md#built-web-runtime).
## Decisions
Optional compiled assets served by the API; no new runtime dependency or development-server fallback.
## Findings
Existing client can use same-origin requests via empty build-time API base.
No client source change or new runtime dependency was needed. The final image separates
migration execution from server startup. Default local Compose remains unchanged.
## Final Result
Completed 2026-09-08 for the built runtime scope. Compiled same-origin browser workflows and
non-root execution are verified. TLS, real secrets, hosted CI and operational recovery remain open.
