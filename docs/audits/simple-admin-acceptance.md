# Simple admin rebuild acceptance audit

Reviewed 2026-09-08 against the approved goal and current checkout. This is a completion
checklist, not a production-readiness claim. The [execution plan](../exec-plans/completed/simple-admin-rebuild.md)
contains dated commands, detailed evidence and recovery archive locations.

| Requirement | Current evidence | Assessment |
| --- | --- | --- |
| Selective Dify reference and license check | Plan records Knowledge/Agent/Human input/Logs references; no copied code | Reference decision recorded |
| Approved design checkpoint | Plan records screens, roles, execution, retained/replaced code and approval | Done |
| Five areas, Work landing, shared run detail | WorkspaceApp routes; Work/Activity use RunDetail; deployed browser journeys | Verified |
| No JSONL or developer workflow prerequisite | Multilingual UI tests register, upload, configure, ask and review through controls | Verified |
| Text/Markdown and pasted knowledge | DocumentEditor validation; knowledge browser tests | Verified |
| Ingestion status, failure recovery, edits and removal | Knowledge module; recorded injected failure and Chrome retry; browser management tests | Verified for tested formats/providers |
| Searchable bounded lists | Knowledge, Agents, runs, models and members have bounded search; review/attempt lists paginated | Main resource lists verified |
| EN/JA/ZH answers and language override | Three multilingual journeys plus requested-language test; deterministic providers | Mock control flow verified; real quality unavailable |
| Exact version citations and excerpts | RunSources, knowledge_versions endpoint, citation-version browser test after edits/deletion | Verified |
| Permission-scoped ready retrieval | Agent knowledge scope, knowledge authorization and restricted-role tests | Verified at tested boundaries |
| Missing evidence and unsafe requests ask for review | Graph routing/guardrails; multilingual unsafe-request review flows | Verified with mocks |
| Viewer/Operator/Admin/Owner | Request schemas, membership authority, migration 0037 and browser tests | Verified; legacy mappings audited |
| Self-promotion and last-owner protection | Hierarchy tests and earlier PostgreSQL concurrency evidence | Verified; current PostgreSQL hierarchy/concurrency selection passes |
| Workspace isolation, including stale browser responses | API denial tests and three delayed-response browser transitions | Verified |
| Initiator and configured agent both constrain actions | task_actions authorization, snapshot/current checks and permission-denial tests | Verified at action boundary |
| Instructions, model, knowledge and two allowed actions | Agent editor/API and core/actions browser tests | Verified |
| Read relevant task history | task_attempt_context supplies five prior IDs/statuses, category and note count | Verified bounded operational history and human corrections reach the drafting prompt; old source excerpts are not reused |
| Bounded steps/time/token/cost | TaskWorkerControl checks before nodes/publication; BudgetedModelProvider reservations | Implemented; current PostgreSQL task/control selection passes; full run completed; isolated test-ID harness error fixed |
| Durable queue and authoritative state | task admission/worker ownership; status, stop and reload browser evidence | Verified; interrupted work fails, not arbitrary graph resume |
| Stop prevents subsequent actions | Stop/action locking tests and recorded active-run Chrome probe | Verified locally; in-flight provider cancellation not guaranteed |
| Exact proposal approval, rejection and once-only effects | Proposal hash and atomic action transaction; browser actions plus prior PG tests | Verified at internal category/note boundary |
| Edit answer, corrected linked attempt | Review form and TaskAttempts; core/actions and prior linked-attempt evidence | Implemented and focused verification recorded |
| Initiator/configuration/status/timestamps/output | Run context, immutable configuration endpoint, saved run; API/CLI/browser tests | Verified |
| Steps/model/provider/latency/tokens/cost/errors/actions | Shared details, trace schema, ledger and action records | Verified for recorded fields; costs explicitly estimated |
| Secrets/sensitive trace fields and observable records | PublicTraceResponse redaction tests; no private reasoning UI | Scoped redaction verified, not universal PII detection |
| CLI named commands and shared authority | Installed CLI evidence has 27 commands; CLI modules/tests use same API | Recorded live evidence; full run completed; isolated test-ID harness error fixed |
| CLI help/scope/JSON/exit codes/noninteractive credentials | parser/main/http/session and CLI tests | Implemented; current regression evidence recorded below |
| UI loading/empty/error/success/focus/responsiveness | Recovery, core, role and 320/768px browser checks | Tested states verified; no comprehensive accessibility audit |
| Small modular implementation and recoverability | Legacy frontend removed with verified archive; source-size gate; 41-table restore drill | Verified local recovery at schema 0037; 41-table restore and application probes passed |
| Architecture/setup/testing/CLI documentation | Owning guides updated; docs gate passes | Standing product/context/quality/UI guides aligned; docs gate verified |
| Compiled app deployment | Current compiled image passed 28 browser tests; UID 10001, no Node/npm, 1372 HTTP outcomes without server errors | Verified; subsequent border-only CSS build/responsive check passed |
| Real provider separately verified or unavailable disclosed | Live API reports no OpenAI key and mock embeddings | Unavailable, disclosed; no quality claim |

## Current verification run

Full backend command: from `backend`, run the repository verification environment's
`python -m pytest -q --tb=short`. Output is captured in
`.artifacts/rebuild-backend-final-suite.log`. The run completed: 665 passed, 107 skipped,
two setup/teardown errors for the same oversized-payload test (839.32s). Pytest embedded
8,000,001 payload bytes in its test ID, exceeding Windows' environment-variable limit.
Explicit short parameter IDs fixed the harness without changing inputs or assertions;
all seven embedding transport tests then passed (0.37s), and Ruff passed. The original full
run was not green; the targeted rerun resolves its sole errored test. A bounded diagnostic
copy is `.artifacts/rebuild-backend-final-summary.log`.
Current compiled browser suite passed 28/28, including version citations. A subsequent
border-only CSS change passed build and responsive browser verification. The current
PostgreSQL task/hierarchy selection passed 15/15 (36.48s).

## Completion assessment and limits

The approved local-first rebuild is implemented and its required mock/browser/CLI flows
have evidence above. The standing product/context/quality/UI guides now describe this app;
old portfolio milestones and UI notes are explicitly historical. Full backend Ruff, 26
repository tooling tests, docs and source-size gates pass. Native controls, keyboard/focus
journeys and responsive views were tested; measured control-border contrast was corrected
and reverified. This is not a comprehensive accessibility certification.

Real-provider verification is unavailable with no key configured, as permitted by the brief's
explicit disclosure requirement. No real semantic quality, provider billing cancellation,
hosted CI, load capacity or enterprise production certification is claimed. These are limits,
not hidden passing checks. Preserve the original failed backend run and its targeted fix;
do not report a clean full-suite rerun that did not occur.
