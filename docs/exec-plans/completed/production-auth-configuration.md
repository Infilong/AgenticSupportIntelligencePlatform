# Reject unsafe production signing configuration

## Goal
Prevent staging/production startup with the public development JWT signing key.
## Context
`backend/app/core/config.py` accepts an arbitrary environment and a public default secret.
Settings are loaded during app startup. The production audit identifies this release risk.
## Requirements
Validate environment names and require a non-default signing secret of at least 32 UTF-8 bytes
for staging/production. Keep local/mock workflows working. Do not print secret values in errors.
## Non-goals
Secret rotation, enterprise identity, TLS deployment, database credentials or full production readiness.
## Acceptance Criteria
Unsafe staging/production configuration fails before serving requests; a supplied valid-length
secret permits startup; typos in environment names fail; existing local authentication tests pass.
## Plan
Settings owns validation; focused backend tests own configuration regressions. Existing auth,
routes, services and database contracts remain unchanged. Document operator setup and limits.
## Verification
Run focused configuration/auth tests, backend lint, then the full backend suite. Exercise the
application import in disposable containers with rejected and accepted production configuration.
## Risks
Length is not entropy. Operators must generate random secrets. Configuration error formatting
must not reveal secrets. Development Compose remains local; no deployment is performed.
## Progress
2026-09-07: inspected settings and startup; identified the default signing-key exposure.
Full backend suite passed 214 tests before five additional edge cases were added. Final focused
configuration suite passed 22 cases; final backend lint passed. Startup import probes rejected
the default key and accepted an in-process random key. Evidence: `.artifacts/20260907-production-config/`.
## Decisions
Enforce staging as well as production and reject misspelled environment names. Retain local,
development and test modes for existing workflows. Do not conflate this guard with secure deployment.
## Findings
The environment field currently has no validation and the signing key is accepted unchanged.
That original finding is repaired. Independent review identified whitespace-wrapped defaults;
the final guard rejects them and tests actual environment loading and 31/32-byte boundaries.
Standard validation error text hides inputs; programmatic error dictionaries still require care.
## Final Result
Completed for the scoped signing-configuration contract. Local authentication regressions pass;
staging/production fail closed for unsafe keys and invalid environment names. No rotation,
database credential or deployment-security claim follows from this guard.
