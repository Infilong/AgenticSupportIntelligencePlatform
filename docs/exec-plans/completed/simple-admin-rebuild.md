# Simple admin rebuild: design checkpoint

## Goal
Deliver the Dify-referenced RAG administration app specified in the user's
goal-objective.md attachment (38ca3a81-937d-4c15-988b-91a47dc6a085).
Status: design approved by the user on 2026-09-08; implementation underway.
Classification: large, cross-cutting, security-sensitive. One implementation owner.

## Context
Inspected 2026-09-08: [architecture](../../../ARCHITECTURE.md),
[frontend guide](../../../frontend/README.md), workspace models/dependencies,
agent routes/service, and the current worktree.
HEAD is 18a977fe4834d39545d71a1e271dd9913cf82a83. Extensive tracked and untracked
changes already exist; HEAD alone is not a backup of the current application.
The existing shell centralizes feature state and rendering. Navigation is tab state,
not URL routing. Execution is synchronous; Redis is not an implemented worker queue.
Existing roles are owner, developer, reviewer, viewer, member, not the proposed four.
Prior test results are not current acceptance evidence for this rebuild.

### Dify references inspected
- [Repository](https://github.com/langgenius/dify): reference for product boundaries.
- [Knowledge](https://docs.dify.ai/en/cloud/use-dify/knowledge/create-knowledge/introduction):
  adopt upload, processing feedback, then retrieval; keep chunk tuning advanced.
- [Agent](https://docs.dify.ai/en/cloud/use-dify/nodes/agent): adopt explicit model,
  instructions, tools, iteration limits; omit marketplace and sandbox agents.
- [Human input](https://docs.dify.ai/en/cloud/use-dify/nodes/human-input): adopt a
  paused execution with clear decision buttons; require authenticated workspace review.
- [Logs](https://docs.dify.ai/en/cloud/use-dify/monitor/logs): adopt searchable history
  and detailed inspection, integrated into our shared run view.
- [License](https://github.com/langgenius/dify/blob/main/LICENSE): reference located;
  no code copied. Any future copying requires checking the exact pinned revision's terms.
References accessed 2026-09-08; documentation patterns, not a vendored Dify release.

## Requirements
Five primary areas; EN/JA/ZH grounded support; fixed roles; bounded agent tools;
human review/cancellation; trustworthy usage records; shared web/API/CLI operations.
Text and Markdown uploads plus pasted text; no JSONL prerequisite for normal users.
Preserve existing data and unrelated changes. No commits or destructive migration.

### Proposed screens and journey
Desktop shell: narrow sidebar, workspace selector, page title, one primary action.
Work layout: task list on the left, selected conversation in the center, execution
details on demand. On small screens these become separate list/detail views.

| Area | Default view | Primary action | Secondary detail |
| --- | --- | --- | --- |
| Work | Needs attention, Active, All task filters | New task | Conversation, review card, run detail |
| Knowledge | Searchable document table with readiness | Add knowledge | Preview, versions, retry, remove |
| Agents | Compact list of configured agents | Create agent | Instructions, model, knowledge, allowed tools; advanced limits |
| Activity | Searchable run table with status, duration, cost | Filter/search | Shared run detail; secondary quality view |
| Settings | Workspace settings | Contextual save/invite | Members and provider settings by permission |

Run detail: result first, sources alongside the answer, then an expandable step
timeline and usage/error details. Both Work and Activity render this same component.
Review appears inside the task with proposed text/action and Approve, Edit, Reject.
Stop remains visible for active runs; it becomes Stopping until acknowledged.
Empty workspace guides Add knowledge -> Create agent -> Start task without a dashboard.
First journey: upload refund policy -> create support agent -> ask refund question ->
inspect citation -> approve proposed internal note -> inspect recorded outcome.
Use URL-addressable screens and task/run IDs; browser Back and refresh preserve location.

### Permission matrix
| Capability | Viewer | Operator | Admin | Owner |
| --- | --- | --- | --- | --- |
| Read permitted tasks, knowledge, activity | Yes | Yes | Yes | Yes |
| Start/stop runs and handle reviews | No | Yes | Yes | Yes |
| Manage knowledge and agents | No | No | Yes | Yes |
| Manage Viewer/Operator membership | No | No | Yes | Yes |
| Manage Admin/Owner roles and providers | No | No | No | Yes |
Server authorizes every operation and tool; effective capability is the intersection
of user permission and agent allowance. Recheck before an approved mutation executes.
Role conversion must be explicit: existing roles are not silently promoted. Keep old
memberships intact until a reviewed mapping is applied; test last-owner concurrency.

### Execution and cancellation design
Task holds conversation; Run is an immutable attempt identity with evolving state.
New attempt links to its predecessor and snapshots agent settings and input.
API persists Queued run and returns its ID promptly. A small worker using the same
backend package claims persisted work; PostgreSQL remains authoritative. Polling by
web/CLI initially avoids a second event infrastructure. No new broker is proposed.
Worker records bounded steps: retrieve/history -> model/tool selection -> evidence
answer or action proposal -> review if needed -> approved internal update -> completion.
Tools initially search knowledge, read permitted history, and propose/apply task
category or internal note changes. No external side effects in this initial tool set.
Durations, model usage, retrieval evidence, errors and decisions are attributable.

Run states: Queued, Running, Awaiting review, Completed, Failed, Rejected, Stopped.
Stopping is a persisted cancellation request while execution is still active.
Review pauses without retaining a live request or occupied worker. Approval queues
continuation from persisted state. Rejection terminates without applying the proposal.
Approval binds action ID, inputs and version; edited proposals invalidate approval.
Internal mutation, application marker and audit record commit in one transaction,
with a unique action ID and run locking to prevent duplicate application.
Stop and mutation use the same locking boundary: after stop is accepted, no new
mutation commits; earlier committed actions remain visible. Check cancellation before
each step/model call and after provider return; attempt provider cancellation where supported.
Worker ownership/heartbeat expiry produces an explicit interrupted failure. Do not
silently replay uncertain provider calls. Retry is a linked new run.
Queued/review states survive restart; accounting preserves uncertain billed attempts.

### Retain and replace
Retain candidates: auth foundation, PostgreSQL/pgvector, knowledge versions/chunks,
retrieval and citation utilities, language handling, provider/accounting boundaries,
audit records and meaningful regression tests. Verify each boundary before reuse.
Replace the current UI shell's product composition with small feature modules.
Move dataset import, prompts, model internals and evaluation out of primary navigation.
Replace synchronous request-owned execution for new tasks with persisted worker runs.
Extend schema additively for task/run/action lifecycle; do not erase historical runs.
Add a thin CLI calling the shared API, with scoped auth, JSON output and exit codes.

## Non-goals
Workflow canvas, custom roles, marketplace, external integrations, arbitrary shell,
autonomous multi-agent teams, microservices, extra document formats and elaborate analytics.

## Acceptance Criteria
All objective requirements remain required, including responsive accessible UI,
bounded/searchable resources, mock labeling and secret redaction.
Chrome proves EN/JA/ZH cited answers, ingestion failure/retry, approved action once,
rejection with no action, active cancellation, correct refresh state and role isolation.
CLI proves login/workspace selection, knowledge add, agent list, task create,
run watch/inspect/stop, and review approve/reject through identical authorization.
Real-provider verification is separate from deterministic mocks; missing evidence
precludes an unconditional completion claim.

## Plan
1. Design approved. Preserve a recoverable snapshot of the dirty tree
   and database before replacement work; record actual snapshot locations and restore procedure.
2. Core journey: feature UI/hooks/client modules, thin API schemas/routes, task service
   and persistence helpers, knowledge and shared run detail; focused boundary tests.
3. Supervision: role migration, worker lifecycle, action approval/atomic application,
   cancellation, budgets and recovery; transaction and permission tests.
4. CLI and release verification: shared HTTP client commands, Chrome journeys,
   multilingual regressions, real provider checks, setup/API/CLI docs and CI gates.
Frontend rendering, state and HTTP access live separately; backend routes, validation,
services and persistence each have explicit owners. New modules normally stay below
300 lines; do not grow existing oversized files. Verify each vertical slice.

## Verification
Run the repository documentation check for this checkpoint. After approval use
[testing commands](../../testing.md), focused backend/CLI tests, build and type checks,
plus actual Chrome evidence for changed user behavior. Add concurrency tests for
approval/stop races and repeated submissions. Never weaken assertions to pass.
Record failing as well as passing evidence and exact commands in this plan.

## Risks
Role migration can change authority; require reviewed mapping. Dirty tree needs a
filesystem snapshot including untracked files, not merely a commit reference.
Preserve database backups before migrations and prove restore before destructive cutover.
Worker crash and provider cancellation do not prove zero billing or exactly-once
external execution. Initial side effects remain transactional internal updates.

## Progress
2026-09-08: Read active objective and current architecture/code; inspected Dify
knowledge, agents, human input and logs. Prepared this concrete design checkpoint.
2026-09-08 after user approval: preserved 672 tracked/untracked source files in
`.artifacts/rebuild-backups/20260908T034029Z/worktree.zip`; every entry verified
against SHA-256 `manifest.json`. Ignored secrets/generated files excluded and left intact.
`database.dump` in the same directory is a PostgreSQL custom-format backup;
pg_restore listing passed (313 entries). Full restore not yet tested.
Restore source by extracting into a separate empty directory, verifying the manifest,
then comparing before replacing any current file. Restore database into a separate
test database first; never overwrite the running database without explicit authority.
Added isolated `/rebuild.html` entry with sign-in, workspace selection/creation, and
knowledge list/upload/edit/delete. Existing app entry remains available during rollout.
New React modules separate session state, API calls, document UI, and file validation.
Vite builds both entry points; no new dependencies or schema changes.
Host preview is on port 5174 (process must be revalidated before reuse).
Chrome verified Japanese add/read and Chinese content update; browser tests cover
file validation, upload, versions, search, removal, refresh, and viewer API denial.
Initial browser run: 1 passed/1 failed due to ambiguous status locator; evidence
preserved under the backup directory's initial-browser-test-failure folder.
Corrected locator targets the exact success message; rerun: 2 passed in 7.8 seconds.
Explicit document language selection added after observing language preservation on edit;
updated language assertion passed in a fresh run: 2 tests passed in 7.2 seconds.
Final Vite/TypeScript build passed. Documentation check and targeted diff whitespace
check passed. Every new source module is below 300 lines. Chrome screenshot inspected
for desktop layout; responsive acceptance and the remaining feature areas are pending.
Workspace URL persistence added and checked in Chrome by switching to the multilingual
workspace and reloading its URL. Latest focused browser suite: 2 passed in 7.1 seconds.
No console errors observed in the final Chrome check. The existing QA workspace retains
one synthetic Rebuild QA policy document; automated cases create isolated test accounts.
2026-09-08 core journey: implemented Work landing, Agents creation/list, Activity,
one shared RunDetail, URL-linked run records and pending answer review in Work.
Review decisions support approving proposed text, publishing edited human text and
rejecting without publication through the existing authorized backend service.
Refresh after review resolution invalidates the pending list and run detail together.
Trace view shows packed evidence, model calls, steps, tokens, estimated model cost,
end-to-end elapsed time and human intervention records. Mock execution is explicit.
Client ignores completion navigation after Work unmounts (including workspace switches).
Current runtime remains synchronous; the interface states that it cannot yet stop execution.
First core regression failed on a non-unique status selector; preserved under
`core-test-initial-failure` in the backup directory. Corrected exact notice selection.
Combined browser suite passed 3/3 in 13.2 seconds. Expanded core test then passed in
8.8 seconds including rejection, durable human-edited answer and page reload.
Chrome confirmed Japanese request d9db174c-7daa-4156-b3d8-a340da3d72f7 completed
with cited Japanese evidence, 0.39 s elapsed, 1105 tokens, $0.000265 estimated model cost.
Chrome review request 7ee4bac3-21bb-4aa3-966e-d1fac070488a was rejected through the new UI.
Final Chrome check showed Rejected with no published answer and no console errors.
Separated elapsed-to-outcome (including human waiting) from summed recorded agent-step
time after reviewing the live rejection. TypeScript passed after this display correction.

2026-09-08 agent instructions: added a bounded instruction field and editor with
name, availability and token budget. Drafting composes snapshotted guidance with the
workspace template; budget planning uses identical composed text. Literal braces
and role-like lines remain instruction text. Shared templates remain unchanged;
the ledger hash identifies the exact prompt and old trace snapshots survive edits.
Focused instruction/provenance tests passed 7/7; agent and budget regression tests
passed 32/32; expanded instruction tests including full graph execution passed 3/3.
Ruff and TypeScript/Vite build passed. Browser suite passed 3/3 in 14.9 seconds,
including instruction save and reload plus cited answers and human review.
Backend image rebuilt and API restarted without schema changes.
Windows verification used `.artifacts/venv-win-rebuild` with locked dependencies;
the existing incompatible backend `.venv` was preserved after uv access failures.
Mock tests establish prompt wiring and records, not real-model instruction quality.
Manual Chrome verification saved and reopened QA Refund Support instructions in
the multilingual QA workspace; the error console was empty.

2026-09-08 model assignment: added a separate paginated/searchable model picker in
the agent editor using existing workspace model and agent APIs. Current assignment
survives filtering; clearing restores default routing. Provider readiness is shown.
TypeScript/Vite build passed. Three focused backend model assignment tests passed
(including foreign-workspace rejection and clearing); browser suite passed 3/3 in
14.7 seconds, proving selection persistence and the selected model in the run record.
All model executions in this verification used deterministic mocks.
Expanded core regression passed in 9.6 seconds with Enter-to-search (no accidental
save) and clearing/reloading the assignment. Chrome showed the empty-model state
and no console errors. Its viewport exposed an editor focus issue; opening the
editor now focuses Name and hides the competing agent list while editing.
Final build and core regression passed (1/1 in 10.1 seconds) after that UI correction.

2026-09-08 Settings: added fifth navigation area with workspace rename and bounded
model search/creation, separated into settings API, workspace UI, model list and form.
Owner permissions govern writes; viewer browser/API denial is covered. New models
are unassigned until selected in Agents; no provider calls occur during setup.
The browser core journey now creates its model through Settings, renames/reloads
the workspace and assigns the model through Agents before checking execution.
Initial test run failed because the viewer assertion was inserted in an owner case;
preserved evidence in `settings-test-placement-failure` under the backup directory.
Moved the unchanged assertion to the viewer fixture; suite passed 3/3 in 16.1 seconds.
Backend model configuration suite passed 10/10. Chrome created synthetic mock model
`qa-settings-support` in QA Real User EN-JA-ZH. Real-provider limits and pricing must
be entered explicitly; credentials are still deployment-managed. No paid calls made.
Member management and target role migration remain required.

2026-09-08 hierarchy and members: added Admin/Operator enum labels in revision 0033,
without mapping or promoting legacy memberships. Viewer is the default new membership.
Fixed-role permissions live separately; membership routes are extracted from the oversized
workspace controller. Admins may manage only Viewer/Operator targets and assignments.
Workspace-row locking serializes membership writes; actor/target authority is refreshed
under that lock. Leave uses the same lock and last-owner guard. Settings now supports
bounded member search, add, role change and confirmed removal using these APIs.
Fresh pre-migration backup: `database-before-roles.dump` in the existing backup directory.
The local API now reports revision `0033_admin_operator_roles`. Downgrade refuses rather
than silently relabeling memberships; use forward repair or verified backup restoration.
Auth/hierarchy suite passed 31/31. PostgreSQL tests passed for legacy preservation,
explicit Admin assignment, simultaneous owner departure and stale Admin denial.
The historical 0032 migration test now targets 0032 explicitly instead of moving head;
its preservation/downgrade assertions remain intact and passed against PostgreSQL.
Updated one old permission-denial assertion from owner-only to members:manage, retaining
403 and adding the required permission assertion. Initial browser member test used
uppercase email while responses normalize lowercase; preserved failure under
`membership-email-fixture-failure`. Corrected synthetic fixture; member test passed
in 5.6 seconds. The other three browser journeys passed against the migrated API.
Build, scoped Ruff and documentation checks passed. Legacy membership conversion is
still pending explicit per-member owner decisions; no silent role conversion occurred.

2026-09-08 task admission: added SupportTask and TaskExecution models and revision 0034.
Admission creates the task, queued GraphRun and initial configuration snapshot in one
transaction. Request keys bind to caller/agent/message/language; duplicate requests reuse
the same task/run, while changed payloads fail. Workspace authorization is rechecked under
the workspace lock after default policy setup. Unavailable/foreign agents are rejected.
Run preparation now supports flush-only mode; the existing synchronous caller keeps its
original commit behavior. No new HTTP endpoint or browser path is exposed before worker
integration; the live database remains on 0033.
Six admission/instruction tests passed: persistence, idempotency, foreign access denial,
injected storage failure rollback and existing instruction execution. PostgreSQL migration
test passed in 10.11 seconds: upgrade from 0033, empty downgrade/re-upgrade, simultaneous
duplicate admission (one task/run), and data-preserving downgrade refusal.
Worker ownership, execution, stop and API/UI integration remain the next required slice.

2026-09-08 stop boundary: added durable task stop requests with authorization, atomic
audit/checkpoint, idempotency and explicit Stopping for active execution. Queued and
review-waiting work transitions to Stopped; pending reviews are closed without an answer.
Finished work cannot be rewritten by stopping. Task-backed review resolution now takes
the run lock after the review lock, matching stop's lock order and preventing late publication.
Seven focused stop/admission tests passed. PostgreSQL stop-versus-review and existing
review transaction tests passed: only one outcome wins and stopped work has no final answer.
No worker acknowledgment, stop endpoint or UI is exposed yet; active cancellation remains
incomplete until the worker is integrated. These changes are not deployed to the live API.

2026-09-08 worker execution: added task worker and node-boundary control modules plus
`python -m app.worker` entry. The graph builder moved out of the oversized runner and
accepts a before-node guard. Existing synchronous callers retain the same graph topology.
Worker ownership uses a PostgreSQL session lock and the owned connection for run state,
steps and publication. Embedding runtime accepts that connection's engine for its separate
accounted embedding ownership. The worker rechecks stop, role, workspace and agent state,
and enforces step/time limits before nodes and publication. Orphaned running work fails
as interrupted rather than replaying model calls. Stop remains pending during a synchronous
provider call, then acknowledges before later graph nodes. No zero-billing guarantee.
Eight PostgreSQL worker/stop tests passed in 7.80 seconds: real graph-to-review execution,
no replay, second-owner exclusion, active stop, revoked permission, step/time limits,
propagated node failure, and stop/review publication serialization. Thirty-three existing
agent/instruction/budget tests passed in 23.51 seconds. Mock providers used throughout.
Task endpoints, Compose worker startup and browser polling/stop integration remain pending;
the live app remains synchronous on migration 0033 until that slice is verified.

2026-09-08 asynchronous app integration: added task creation, task-run read and stop
HTTP endpoints with existing permission dependencies; Work now admits durable tasks
and polls shared run details. Unchanged in-form retries retain their request key.
Selected-agent state no longer resets when history refreshes. Stop is shown only for
task-backed runs; Queued/Stopping/Stopped history filters and stop intervention records
are visible. Review and history refresh when the selected run reaches its outcome.
Compose starts the worker after API health/migration readiness. Preserved
`database-before-tasks.dump` beside the existing backups before applying revision 0034.
Six API/control tests passed; expanded API checks passed 2/2 including queued filtering.
All four browser journeys passed against the asynchronous stack in 23.9 seconds.
Expanded core test passed in 15.7 seconds for stop, pending-review removal and reload;
final stop-history assertion passed in 15.6 seconds. TypeScript/Vite, scoped Ruff,
documentation and diff-whitespace checks passed.
Chrome Japanese run 06d93fff-3edd-4ebe-b5d0-123fa438b067 completed with cited Japanese
evidence, 0.55 seconds to outcome, 1178 tokens and $0.000301 estimated mock-model cost.
Chrome stopped review run 961165c4-c1d2-45dd-b399-85d104706a0c without publishing an
answer; pending review disappeared and the stop persisted after refresh.
Active mid-step stopping remains proven by PostgreSQL worker tests, not yet by a
Chrome active-provider demonstration. Real-provider acceptance remains unverified.

2026-09-08 agent knowledge access: Agents now offers all/selected/none knowledge with
bounded search and up to 100 selections. The backend validates workspace-owned references,
snapshots settings and filters candidates in SQL before content enters retrieval/model context.
Empty selection provides no evidence and routes to review. No migration required.
Focused retrieval/graph checks passed 20 tests with 4 PostgreSQL checks initially skipped;
the PostgreSQL-enabled version/failure rerun passed all 7 tests in 18.70 seconds.
Four rebuild browser journeys passed in 26.1 seconds, including selection persistence,
cited answer, stop, ingestion and role enforcement. Build, scoped Ruff, docs and diff checks pass.
Chrome run 76832cb1-afe6-48f4-b61d-876120da3939 used the selected English document:
0.51 seconds, 789 tokens, $0.000199 estimated mock-model cost; no browser console errors.
The selected checkbox persisted after navigation; the QA agent was restored to all documents
after verification to preserve multilingual QA. Form layout was visually inspected; final
polish should reduce its height and remove the temporary legacy navigation escape.
Real-provider quality, internal approved actions, linked attempts and CLI remain unverified
or unimplemented; this evidence does not establish full-goal completion.

2026-09-08 action transaction foundation: added explicit allowed category/note settings,
canonical input/hash schema, immutable proposal and unique-note models, revision 0035,
and task_actions service. Proposal staging does not apply changes. Approval checks exact
hash and current reviewer, initiating user and current/snapshotted agent authority.
Task update, resolution and audit commit atomically; repeat approval returns the stored result.
Eleven action tests passed in 6.40 seconds; two PostgreSQL races passed in 3.20 seconds
for duplicate approval and stop. Seventeen migration/action/stop/knowledge checks passed
in 33.40 seconds before the final independent-reviewer regression was added and verified.
Migration test preserves a multilingual task across upgrade/empty downgrade and refuses
to remove applied action history. Ruff, documentation and diff checks pass.
Not deployed: live app remains on 0034. Next integrate proposal generation, action trace,
endpoints and shared review controls, ensuring answer approval cannot bypass action approval.
No browser or real-provider evidence for internal actions yet.

2026-09-08 action worker/API integration: guarded graph publication stages category/note
proposals from accounted classification/draft outputs. It routes to review without applying
updates. Action read/resolve endpoints enforce workspace permissions and exact hashes;
answer review cannot bypass pending actions. Rejecting an answer or stopping rejects pending
proposals. Applied actions add ordered step/tool records within the same transaction.
Two API tests pass; full mock worker tests prove guarded proposal-to-approval-to-answer.
Initial PostgreSQL regression exposed a workspace FOR UPDATE versus checkpoint FK deadlock
(9 passed/1 failed); preserved in `.artifacts/task-action-stop-deadlock.txt`. Stop/action
locks now use FOR NO KEY UPDATE, retaining mutation serialization while allowing FK checks.
Seventeen PostgreSQL worker/review/stop tests pass in 19.07 seconds; a deterministic held-stop
lock regression passes in 1.33 seconds. Seventeen action/control/API unit checks also pass.
No deployment/browser action evidence yet; next add agent action controls and shared review UI,
then back up, apply 0035, and verify Chrome approval, rejection, stop and persisted results.
Existing human review, citation-integrity and step-order regression: 28 passed in 42.10 seconds.
Scoped Ruff, documentation and diff-whitespace checks pass.

2026-09-08 browser action integration: Agents exposes category/note capabilities; Work
review shows exact proposals and requires their resolution before answer publication.
Rejecting the request remains available and discards pending actions. Shared execution
records collapse action details to avoid repeating full notes alongside the review form.
Action reviews are labeled Review request. TypeScript/Vite passes; all five rebuild browser
journeys pass in 36.5 seconds, including approval, refresh, rejection and stop. The final
collapsed-layout action rerun passes in 11.9 seconds.
Preserved database-before-actions.dump (330 archive TOC entries) before deploying API/worker
on migration 0035. Chrome approval run 8f00938a-2713-4b09-87b3-75c6559385c6 completed;
database confirms two applied proposals and exactly one note. Chrome rejection run
d4e2ebdb-9798-4859-bd29-b9bfa86dce02 and stop run c823b7fa-603e-441c-b07c-8c6d4c290f4c
each retain two rejected proposals and zero notes. No Chrome console errors.
Known state debt: answer rejection is still stored as failed/human_rejected and displayed
as Rejected; make durable task API states consistent without silently rewriting legacy history.
Linked attempts/task history, CLI, final UI/role rollout and real-provider acceptance remain.

2026-09-08 linked-attempt backend: extracted review outcome persistence from the oversized
review service; new durable task rejections persist rejected, while legacy history remains
unchanged. Twenty-seven API/review regression checks passed in 43.41 seconds.
Retry admission now creates a linked run for the existing task, checks terminal parent and
absence of active siblings, snapshots current authority/config/budgets and saves corrections.
Separate task_attempts metadata preserves old task schema semantics. Original request replay
returns the first run; retry keys deduplicate within retry admission. Corrected draft prompts
include bounded status/category/count history, never old evidence text. Identical approved
notes are reused under the task lock and expose reused=true in the result.
Nine retry unit/PostgreSQL tests passed in 13.93 seconds, including full worker prompt capture,
competing retries and no duplicate notes. Four concurrency/migration checks passed in 28.66
seconds: preserved earlier notes, safe empty 0036 downgrade and populated-history refusal.
Ruff passes. Not deployed: current app stays on 0035. Next add retry endpoints, parent/history
links and corrected-instruction UI, then verify release and Chrome/CLI integration.

2026-09-08 retry API/browser rollout: added permission-gated retry and bounded history
endpoints, parent/correction fields on task-run reads, and shared-record New attempt controls.
History navigation retains the current correction independent of the paged list. Failed and
Rejected filters are separate; reused notes have an explicit display result.
Nine API/admission checks passed in 6.82 seconds; TypeScript/Vite and Ruff passed. All five
browser journeys passed in 39.2 seconds, including retry completion, refresh and parent/child
navigation. Backed up database-before-attempts.dump (349 TOC entries) before applying 0036.
Chrome child 5004c0d6-2d1a-4872-a671-95e56ff058c8 completed with saved correction; database
confirms parent c823b7fa-603e-441c-b07c-8c6d4c290f4c remains stopped. Follow-up
64067172-b91d-4f89-9ebf-f9778a13853e displayed prior-note reuse; SQL confirms one note for
the task and reused=true in the action result. No Chrome console errors during retry inspection.
Current next stage: practical CLI followed by final UI/role rollout and release acceptance.

2026-09-08 CLI implemented in small standard-library modules for parser, commands, HTTP,
sessions and output. Backend packaging exposes asi; python -m app.cli also works. Login
uses hidden input/stdin, DPAPI on Windows or owner-only POSIX storage, and API-bound sessions.
Workspace selection is explicit; versioned JSON, request-key retention and documented exit
codes support automation. Watch stops at review without approving. Exact action hashes
are required for action decisions; all operations use the same API and permissions.
Fourteen tests passed in 2.86 seconds; live installed CLI acceptance passed 27 commands in
dedicated workspace fb1e2db3-e503-45bb-bd94-54265b00eafa, covering the named core operations,
human decisions, stopping and permission denial. Evidence: .artifacts/cli-live-evidence.json.
CLI runtime has no new dependencies. Local packaging used the already-declared setuptools
build dependency after resolving cache/network access. Usage and safety contracts live in docs/cli.md.
Remaining: final UI/role rollout and full release acceptance, including real-provider limits.

2026-09-08 default UI rollout: / now opens the five-area workspace; /rebuild.html
remains compatible with saved links. /legacy.html preserves historical workflows without
a main-navigation link. Legacy browser tests now explicitly target that entry; assertions
remain unchanged. Fixed Skip to content to focus main without changing the hash route.
Five remake journeys passed (39.1s); core including keyboard focus plus eight legacy
session-recovery checks passed (38.2s). TypeScript/Vite build passed. Rebuilt only the
Docker frontend and inspected the main URL in Chrome; no errors on the authenticated
host-dev landing page. Live role counts included 104 legacy reviewers; no authority was
silently changed. Explicit owner reassignment remains supported. Release acceptance pending.

2026-09-08 recovery acceptance: extended the existing restore application probe from legacy
synchronous runs to durable task admission/replay, worker execution, history reads and queued
stop without model calls/actions. Live drill passed in 34.546s at 0036_task_attempts: all 41
table counts/content fingerprints matched, source unchanged, EN/JA/ZH application checks
passed. Temporary database cleanup independently verified. Artifact:
.artifacts/database-restore-34ffe983d12d47f38dc06f10fa1ceb45/report.json.
Two harness tests and Ruff passed. This closes local logical restoration evidence for the
current schema; real-provider quality and active-call browser cancellation remain separate.

2026-09-08 Chrome active-stop acceptance: delayed a mock provider response in a temporary
single-run worker and stopped fc0559c6-af82-43d6-9850-b1f83451f651 through the UI.
Observed Running -> Stopping -> Stopped; reload retained partial accounting and no final
answer. SQL: zero actions/notes, no steps after classification. Normal worker restarted.
Fixed a discovered stale list status by refreshing on active transitions as well as settlement.
Controlled browser status regression plus core journey passed 2/2 (23.1s); build passed.
No real provider call was made; live provider cancellation remains unverified.

2026-09-08 ingestion recovery verified in Chrome: controlled KnowledgeService embedding
failure preserved document 4223378d-995c-4f75-b7f4-39a5455f1362 and its text. Browser Edit
and retry returned Ready/version 2 with no error; SQL confirmed two versions and one chunk.
The failure was injected only in a one-use service probe; normal API settings stayed intact.
Rewrote the README around the delivered five-area app, role hierarchy, durable tasks, CLI,
setup and verified limits, replacing the outdated dataset-first demo and stale test counts.

2026-09-08 requirement audit found that run/user/agent IDs were persisted and returned by
GraphRunResponse but omitted from the UI. Added collapsed Run context using existing API
fields, with explicit unavailable labels for absent historical values. Core browser assertions
compare shown IDs to the admission response. Core/status tests passed 2/2 in 21.3s; build
passed. Live API reports provider_key_configured=False and embedding_provider=mock;
no credentials were printed and no real-provider calls were attempted.

Remaining audit work (not completion claims):
- Agent configuration snapshots are persisted in TaskExecution but not inspectable in the
  new execution view; assess safe selected fields rather than exposing raw settings.
- Verify responsive layout and wider keyboard behavior in all five areas.
- Resolve fixed-role transition: legacy reviewers still exist; avoid silent privilege grants.
- Audit current trace redaction and source/version usability against the exact brief.
- Complete a requirement-by-requirement evidence review; older narrow tests are not blanket
  production evidence. Real-provider checks are unavailable with current configuration.

2026-09-08 responsive acceptance found and fixed 156px phone overflow with long names.
Grid/form controls now shrink within the viewport; actions wrap, header buttons retain width,
and phone navigation exposes every area over multiple rows. Five-area 320px/768px browser
regression plus knowledge/agent editing passed; screenshots reviewed. Failure evidence retained
in .artifacts/responsive-initial-failure. Final CSS rerun passed (4.8s); frontend rebuilt.
Broader keyboard and populated execution-state accessibility remains part of final audit.

2026-09-08 searchable-list audit found Agents was paginated but lacked the search control
already supported by the API. Added submitted search with page reset and a distinct no-match
state, retaining bounded server-side results. Input length matches the 120-character API
contract. Live browser tests verify no-match and matching results before opening an editor
at phone/tablet widths. Core plus responsive/search checks passed 2/2 (19.9s); build passed.
Frontend rebuilt. Configuration snapshot visibility and final security/role audit remain open.

2026-09-08 trace audit found no redaction at the graph trace response boundary. Added a
small serializer base and recursive response redactor covering structured secrets/PII keys,
email addresses, known token patterns and credential assignments, including JSON strings.
No stored evidence or mutation inputs are rewritten. Three new unit/API tests plus existing
agent tests passed 27/27 (42.28s); Ruff passed. API rebuilt after confirming zero active runs.
Limits are explicit in observability-design.md: this is neither universal PII detection nor
storage encryption, and other resource APIs retain their separate access contracts.

2026-09-08 saved task configuration now has a workspace-scoped read endpoint and an
explicit whitelist schema using response redaction. The UI loads it only when Agent
configuration at start is expanded; CLI run inspect includes the same record. No migration
or snapshot rewrite. Four API/schema/task tests passed (6.33s), fourteen CLI tests passed
(2.97s), Ruff and frontend build passed. Live installed CLI inspection returned original
settings (.artifacts/cli-snapshot-evidence.json); deployed core browser journey passed
(18.9s). Tests prove later agent edits do not change saved instructions/name/knowledge/actions,
and foreign/anonymous reads are denied. Model assignment is the saved configuration ID;
actual provider/model selection remains in model call records.

2026-09-08 role audit: 31 hierarchy/auth/workspace tests passed (22.43s); real PostgreSQL
role migration, competing owner departures and stale-admin revocation test passed (4.41s).
Confirmed legacy roles remain accepted by request schemas, not merely stored historical data.
User explicitly authorized removing unnecessary legacy system paths in response to the
transition question. This supersedes indefinite compatibility preservation as the end state.
Retirement work must preserve accounts, knowledge, task/audit history and a recovery backup.
Dependency inspection found production legacy-role references concentrated in the role enum
and permission map; 16 browser navigation calls still exercise the legacy HTML entry.
Next retirement slices: fix the four-role assignment contract and migrate existing role
assignments with documented permission effects; remove legacy UI entry/code after porting
any still-relevant recovery/isolation checks to the new app. Do not delete shared transport
modules imported by the new UI or discard protected-data regression coverage blindly.

2026-09-08 legacy retirement first slice: membership add/update request schemas now accept
only Viewer/Operator/Admin/Owner. Owners cannot assign retired roles either (422). Existing
response schemas still read historical memberships until migration. The UI requires an explicit
supported choice when editing a legacy assignment. Updated public-API test fixtures to
Operator; retained denial, owner guard, archive and resource-boundary assertions. Hierarchy,
auth/workspace, evaluation and guardrail tests passed 51/51 (85.17s); Ruff/build passed.
Legacy browser fixtures still using Reviewer require porting to the current role model and UI;
they are not counted as passing. Next: membership data transition and legacy frontend removal.

2026-09-08 ported restricted-role browser checks to the new UI and durable tasks. Viewer
and Operator journeys passed (10.7s), preserving retrieval/workspace denial and no-side-effect
assertions. Added explicit Viewer task stop/admission denials and Operator allowed admission,
stop and review rejection. Removed obsolete Reviewer dashboard test after replacement passed.
No legacy-role API browser fixture remains in these checks. Legacy data migration and the
remaining old interface dependencies still require retirement.

2026-09-08 membership retirement deployed at migration 0037. Disposable PostgreSQL test
passed (6.03s): all three legacy mappings, audit records, preserved accounts/workspace,
constraint rejection and downgrade refusal. Ruff passed. Pre-migration backup and restored
application checks passed for all 41 tables and EN/JA/ZH durable workflows in
`.artifacts/database-restore-a7c6b62898de425da84630a2dee55c39/report.json` (35.688s).
Live migration converted 104 Reviewer memberships into Operator and inserted 104 audit
records; no legacy memberships remained. API healthy. Deployed membership and restricted-role
browser checks passed 3/3 (14.3s), including workspace isolation. Public permission matrix
now exposes only the four assignable roles; hierarchy/auth tests passed 31/31 (22.81s).
Historical enum decoding and legacy UI code remain pending cleanup, not new assignable roles.

2026-09-08 legacy test retirement continuation: ported eight session recovery and three
workspace response isolation checks to the main interface. All 11 passed against the
deployed app (27.4s). Preserve failure feedback/drafts, invalid-session clearing, bootstrap
503/network retry, protected 401/403 distinctions, corrected password retry, and delayed
old-login rejection. Isolation now also distinguishes stale A data during A-to-B-to-A
return visits, checks current drafts remain intact, and checks selected workspace identity.
Initial two failures were old standalone-text locators on alerts containing a Retry button;
visible errors were confirmed in snapshots. Evidence retained under
`.artifacts/session-recovery-port-initial`. No product source change was required.
Remaining legacy specs and UI entry still need retirement; language-choice coverage currently
depends on an old UI selector absent from the new composer and needs a product-aligned replacement.

2026-09-08 response-language gap closed: Work now exposes Auto/English/Japanese/Chinese
and passes the choice to existing task admission. Request identity includes language so
unchanged failures deduplicate while a changed language starts a distinct request. Ported
the legacy language-choice browser test to task admission, authoritative worker trace and
shared run detail. Explicit Japanese kanji-only answer and automatic detection provenance
passed; injected 503s proved retained choice and stable/changed retry keys. Build passed;
language/core/responsive browser suite passed 3/3 (27.5s) on deployed localhost:5173.
Reviewed the 320px Work screenshot: selector and form fit without horizontal overflow.
This tests mock execution, not real-provider multilingual quality. No backend schema change.

2026-09-08 legacy browser retirement: replaced the old multilingual screen tour with three
main-interface EN/JA/ZH journeys. All passed (25.4s), covering UI registration/workspace,
ingestion, grounded response/language, source/model/cost visibility, shared Activity detail,
reload, review text-field focus and durable rejection. Bootstrap recovery remains in the
dedicated passing recovery suite. Retired four obsolete screen specs (folder patch, fading
toast, reconciliation panel and combined legacy UX). Exact pre-removal copies verified in
`.artifacts/legacy-browser-tests-before-retirement.zip`. No backend test was removed.
Initial migration-test assumptions (language before worker execution and old cost label)
were corrected against authoritative traces/rendered output; failed artifacts retained under
`.artifacts/multilingual-port-initial` and `.artifacts/multilingual-port-cost-label`.
The legacy UI source/entry is the next cleanup boundary; no browser spec now navigates to it.
Full remaining Playwright suite passed 27/27 (1.9m) against localhost:5173; this includes
three API-only legacy workflow regressions as well as current browser journeys. TypeScript,
documentation-map validation and diff whitespace checks passed. This does not prove final
release readiness or real-provider quality; the requirement audit remains open.

2026-09-08 legacy frontend source retired: removed 36 obsolete files (18,426 lines),
including the old shell/pages/hooks/styles and legacy.html. Verified exact recovery ZIP
and SHA-256 manifest under `.artifacts/legacy-frontend-retirement/` before deletion.
Retained shared `app/apiRequest.ts` and all new UI modules; removed Vite's legacy build
entry. Build passed with 41 modules, no legacy bundle; deployed updated frontend.
Updated frontend/code-map/architecture ownership and removed obsolete size exceptions.
Size gate also required tightening pre-existing backend shrinkage; no source limit increased.
Docs gate and size gate passed (215 checked files, 300-line default). No database changes.
Post-deployment full Playwright suite passed 27/27 (2.0m), including multilingual journeys,
actions, role controls, responsive views, recovery and workspace/session isolation.

2026-09-08 version-linked citations delivered: RunSources uses recorded document IDs and
version numbers, with excerpts retained in the shared run view. Links open read-only saved
versions in Knowledge; navigation and reload preserve identity. New knowledge version route
checks knowledge permission plus document/version workspace scope; deleted/missing resources
return 404 rather than substituting current text. No schema migration or model call needed.
Backend version/auth boundary suite passed 7/7 (13.80s); Ruff/build/docs/size gates passed.
Deployed citation plus EN/JA/ZH browser suite passed 4/4 (30.6s): run against v1, edit to v2,
open v1, reload, Back to run, deletion error; multilingual answers/review remain intact.
Historical traces without structured source identity retain excerpts without invented links.

2026-09-08 completion audit started in [acceptance checklist](../../audits/simple-admin-acceptance.md).
Compared the full brief with current routes, UI, task control, reservation and CLI modules.
Corrected stale quality/limitations text about the removed frontend and Costs UI. Live API
readiness still reports no OpenAI key and mock embeddings. No provider credential was printed.
Full backend suite is running in unified exec session 12852; output is
`.artifacts/rebuild-backend-final-suite.log`, last observed 18% with no displayed failures.
Revalidate this handle before continuing; do not restart while it remains live. Required
follow-ups are useful bounded task history, compiled deployment/current-schema restore,
final browser/accessibility and documentation checks. Docs/diff checks pass.

2026-09-08 compiled deployment and recovery verified. Fixed missing worker startup in
compiled-image runbook and verification harness; failure cleanup test verifies only generated
API/migration/worker containers are removed. Four harness tests and Ruff passed. Compiled
image passed all 28 browser tests (48.9s), production UID 10001, no Node/npm runtime,
1372 HTTP outcomes with zero server/errors. Artifact: `.artifacts/built-web-294396af4e1c4a83807efbfd62ab5b25`.
Worker remained running; all probe containers cleaned. Existing Compose worker also remained available.
Schema-0037 restore passed with 41 table manifests and EN/JA/ZH application probes (40.063s),
archive/report at `.artifacts/database-restore-f8a2e72eb5af40b1b9d72112e7c00a32`.
Contrast review found input borders 1.46:1; changed control borders to #718477, measuring
3.52–3.99:1 against checked backgrounds. Build and responsive browser test passed (5.8s),
320px screenshot reviewed. This CSS-only change follows compiled-image evidence.
Full backend session 12852 remains live, last observed 55%, with two E results pending details.
Do not restart it; inspect final log and fix the errors before release acceptance.

2026-09-08 PostgreSQL final selection passed 15/15 (36.48s), covering hierarchy,
admission, worker ownership/limits, stop, concurrent retries and approved actions. Output:
`.artifacts/rebuild-postgres-final-suite.log`; session 3201 completed successfully. Full
backend session 12852 remains live at 93%, with two setup errors pending final diagnostics.
Reviewed task_attempt_context plus AgentPromptService and test_task_attempts: bounded prior
statuses, category, note count and human correction reach the drafting prompt as task data.
This satisfies operational task-history context without reusing prior source excerpts that
could bypass the current knowledge selection. No new history feature is necessary.

2026-09-08 full backend run finished: 665 passed, 107 skipped, two setup/teardown
errors on the same embedding oversized-body parameter (839.32s). Cause: pytest used the
8,000,001-byte body as test ID and exceeded Windows' 32767-character environment-variable
limit. Added short IDs only; all seven embedding transport tests passed (0.37s), Ruff passed.
Original inputs/assertions unchanged. Preserve full log; use bounded summary
`.artifacts/rebuild-backend-final-summary.log` to avoid emitting the enormous parameter ID.
Sessions 12852 and the log-inspection process are terminal. PG selection separately passed
15/15. Remaining audit work: correct standing product/context docs and final consistency review.

2026-09-08 final standing-document audit: replaced superseded product/context scope,
rewrote quality score from current evidence, labeled portfolio milestones and old UI notes
historical, and preserved originals in `.artifacts/standing-docs-before-final-alignment.zip`.
Full backend Ruff passes; all 26 repository tooling tests pass (0.859s). Reviewed current
requirements against implementation, browser/CLI evidence and schema-0037 recovery. No
required local mock flow remains unimplemented. Real-provider checks are unavailable and
explicitly disclosed rather than counted as verified quality.

## Decisions
2026-09-08 approved legacy membership retirement: Reviewer maps to Operator;
Member/Developer map to Admin. These authority changes are explicit, audited and backed up.
Retain historical records; retired enum labels can still decode old records but a database
constraint blocks new legacy memberships. This supersedes the initial compatibility policy.
2026-09-08 linked-attempt design: keep the same support task and create a new run linked
to its parent. Retry admission rechecks current permissions, agent configuration and budgets;
the parent must be terminal and no attempt for the task may remain active. A request key
deduplicates admission, including retries after lost responses. Corrected instructions affect
only the new run and retain exact prompt provenance. Prior attempts and applied actions are
not rewritten or replayed. A bounded history snapshot provides prior statuses/category and
counts, not old evidence that could bypass the new knowledge selection. Schema additions
need preservation/concurrency tests before deployment; API/UI follow the admission boundary.
2026-09-08 internal action implementation sequence: first add immutable category/note
proposals and transactional resolution, then wire bounded graph proposals, endpoints and
shared review UI. Agent settings explicitly opt into each action; missing settings deny
mutations. Approval submits the exact proposal hash, rechecks initiating user, reviewer,
current agent and snapshotted capability, and serializes with stop under the run lock.
Action result, task mutation and audit commit together; repeated approval returns the
same applied result. New inputs require a new proposal and approval. No external actions.
Schema additions remain undeployed until migration and concurrency verification passes.
Proposed: new modular UI using the existing stack; one backend package and database;
small persisted worker; shared API with polling; internal task updates only initially.
User approval received; continue implementation without another design gate.
The isolated entry is temporary rollout scaffolding, not final product navigation.

## Findings
Initial inspection found role and synchronous-execution gaps. New Work now uses durable
tasks and a worker. The legacy frontend is removed and recoverable from the recorded archive;
legacy memberships migrated to the approved four-role hierarchy with audit history.
Mock tests prove control flow and permissions, not real-provider answer quality or readiness.

## Final Result
Completed the approved local-first five-area RAG/agent admin rebuild. Shared web/API/CLI
operations enforce four-role scope, exact human approvals, bounded durable execution, stop,
linked retries, version citations and observable records. The old frontend is removed with
verified recovery archives. Current evidence: compiled browser 28/28; full backend 665 pass
and 107 skip with its one oversized-ID case resolved by a seven-test rerun; PostgreSQL
selection 15/15; tooling 26/26; build, full backend lint, docs and size gates pass.
Schema-0037 logical restore and application probes pass. A later control-border-only CSS
change passed build/responsive checks and measured contrast. No commit was created.

Real provider unavailable (no key configured). Mock results do not verify real semantic quality,
provider cancellation/billing, hosted CI, load capacity or enterprise production readiness.
The [acceptance audit](../../audits/simple-admin-acceptance.md) records these qualifications.
