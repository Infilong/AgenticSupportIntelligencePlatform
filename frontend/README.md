# Frontend guide

## Default admin interface

`/` opens the five-area admin interface. `/rebuild.html` remains a compatible entry for saved links.
The obsolete interface and its HTML entry have been removed after porting relevant browser checks.
`src/rebuild/WorkspaceApp.tsx` owns session/workspace selection; `api.ts` owns typed
requests; `knowledge/` owns document management and the file editor. `work/` owns
agent creation, requests/history, shared run details and pending answer review.
`work/AgentEditor.tsx` edits name, instructions, model, availability and token budget;
the API persists instructions for new run snapshots without changing old runs.
`work/AgentModelPicker.tsx` owns bounded model search, readiness labels and selection;
an empty assignment restores workspace routing. The backend validates workspace ownership.
`workspace.css` owns the app styles. Vite builds the main and saved-link HTML entries.
Work is the default route; Knowledge, Agents, Activity and Settings use hash navigation, and
run IDs are reloadable links. `settings/` separates workspace renaming, model creation/list,
and transport. Provider credentials stay on the backend; live-model limits/prices require
explicit input. `settings/Members.tsx` owns bounded member search, add, role changes
and confirmed removal. Admins manage Viewer/Operator memberships; owners also assign
Admin/Owner. Migration 0037 converts legacy memberships to the approved four-role hierarchy;
the API rejects retired roles for new assignments.
Work now submits durable tasks; `work/useRunTrace.ts` polls queued/running/stopping records.
The Work composer defaults to automatic response-language detection, with explicit English,
Japanese and Chinese choices. The selection travels through the same task API as CLI requests;
changing it changes submission identity, while unchanged failed submissions retain their key.
RunDetail offers Stop for task-backed runs and shows stop history. Request keys survive
unchanged retries within the current composer. Legacy runs remain readable.
`work/AgentKnowledgePicker.tsx` owns bounded document search and all/selected/none access.
The backend validates selected document ownership and filters retrieval before loading context.
`work/AgentActionPicker.tsx` configures category/note proposals. `work/TaskActions.tsx`
shares exact-input review controls and collapsed action records. Answer publication waits
for action resolution; rejecting the request also rejects pending actions. Backend checks
remain authoritative. These internal actions are deployed on migration 0035.
`work/TaskAttempts.tsx` owns corrected-instruction submission and bounded task-history
navigation. The shared record links parent attempts and displays saved corrections even
when the history list is paged. Retry keys survive unchanged in-form retries. Migration 0036
supports these routes; previously applied identical notes display an explicit reuse result.
The [rebuild plan](../docs/exec-plans/completed/simple-admin-rebuild.md) records scope,
backups, acceptance and pending work. Run `npm run build` and
`npm run test:e2e -- rebuild-core.spec.ts rebuild-knowledge.spec.ts --workers=1` against the intended server.
Workspace IDs in the URL are checked against server-returned memberships before use;
switching workspace unmounts feature state and rejects late read results.
`work/RunSources.tsx` renders recorded excerpts with links to their document/version identity.
Knowledge opens those links in read-only `DocumentVersionView.tsx`, retaining the URL across
reloads. Later edits do not substitute the latest text; deleted or inaccessible versions
show an error. Browser Back returns to the run. Old traces without source IDs keep excerpts.

## Transport and deployment

`src/app/apiRequest.ts` is the retained shared HTTP transport. It reports status-bearing
errors and validated server request IDs. Authenticated 401s expire the matching session;
403, network and server failures preserve it. Workspace/session changes unmount feature
state; already-dispatched backend mutations can still finish in their original workspace.

The optional [built web image](../infra/README.md#built-webapi-image) serves compiled assets
and API from one origin. Local Compose uses Vite without a source bind mount. Rebuild it
with `docker compose -p asi-verification up -d --build --no-deps frontend` after source edits.
A host build alone does not update the running image. No credentials belong in browser config.

## Verification

From this directory run `npm run build`, `npm run typecheck` and `npm run test:e2e` against
the intended running API/frontend. Tests use deterministic providers. Browser journeys cover
EN/JA/ZH ingestion, cited answers, human review, actions, stop, record navigation and reload.
Recovery/isolation tests cover retained drafts, retry, permission failures and delayed old
responses. Responsive checks cover phone/tablet views. These are evidence for tested flows,
not proof of complete accessibility or real-provider quality.

Legacy folder, toast, reconciliation-panel and dashboard tests were retired after relevant
coverage moved to the current interface. Backend evaluation/accounting tests remain separate.
Recovery archives and exact removal manifests are recorded in the rebuild plan. Current UI
modules stay under 300 lines; split by rendering, state and API responsibility when needed.
