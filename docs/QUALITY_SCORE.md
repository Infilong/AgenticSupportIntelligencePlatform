# Quality score

Current status for the approved five-area rebuild, reviewed 2026-09-08. Detailed scope,
commands, recovery locations and limits live in the [acceptance audit](audits/simple-admin-acceptance.md)
and [rebuild record](exec-plans/completed/simple-admin-rebuild.md).

| Area | Evidence | Limits |
| --- | --- | --- |
| Product journey | Compiled app passed all 28 browser tests, including EN/JA/ZH, version citations, reviews, actions and isolation | Deterministic providers; no real semantic-quality claim |
| Backend | Full run: 665 passed, 107 skipped; oversized test-ID harness error fixed, affected 7 tests pass | Original full run was nonzero; targeted rerun resolves its sole errored case |
| Concurrency | 15 current PostgreSQL hierarchy/task/stop/retry/action tests pass | Scoped checks, not load testing |
| CLI | 27 recorded live commands; CLI regressions in backend suite | Core operations, not every settings operation |
| Deployment | Compiled production image, UID 10001, no Node/npm, worker running; 1372 HTTP outcomes without server errors | Local deployment evidence; hosted operations and CI unverified |
| Recovery | Schema 0037, 41-table restore and restored EN/JA/ZH app probes pass | Local logical backup, not offsite disaster recovery |
| Maintainability | Legacy frontend removed; current source-size and full backend Ruff gates pass; 26 tooling tests pass | Some existing backend size exceptions remain |
| UI accessibility | Native labeled controls, keyboard/focus tests, 320/768px browser checks; control borders 3.52–3.99:1 | Tested journey, not a comprehensive accessibility certification |
| Trace privacy/accounting | Scoped redaction, workspace checks and estimated usage records tested | No universal PII detection or billing reconciliation guarantee |

The app is a verified local-first implementation of the approved brief. Do not describe these
results as enterprise or unconditional production readiness. Real-provider verification is
unavailable because no OpenAI key is configured. See [limitations](known-limitations.md).

Earlier production audits and plans are historical or separate workstreams; they must not
silently expand this product. Test artifacts are local ignored evidence. Durable summaries
belong in repository documentation; preserve failed evidence alongside subsequent corrections.
