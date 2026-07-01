# Information Architecture and Navigation Cleanup

## Goal
Reframe the frontend from a numbered support-demo flow into a professional AI platform console for building, operating, evaluating, and governing stateful agents.

## Context
The product direction is Agentic Intelligence Platform. The previous UI grouped pages as Setup, Operate, and Observe with numeric navigation, which made the app feel like a linear demo instead of a production-style platform. This ticket intentionally changes frontend information architecture and copy only.

## Changes
- Replaced numbered sidebar navigation with platform groups: Platform, Build, Operate, Evaluate, and Admin.
- Renamed primary pages to clearer platform concepts: Dashboard, Data, Knowledge, Agents, Runs & traces, Human review, Evaluations, Usage & costs, Prompts, Models, and Audit.
- Updated auth, brand, topbar, dashboard, data, agent, trace, and cost wording to describe an AI agent platform rather than only a support-answer demo.
- Converted the dashboard readiness flow from numeric steps to capability tokens aligned with the sidebar.
- Added honest dashboard coverage cards for Tools, Guardrails, Permissions, and Scale path so users understand what is implemented now versus future product surface.


## Design Review Decision: Canonical Entry Point

Approved during `/plan-design-review`: **Account is the canonical entry point**.

- Account owns user identity, workspace creation, workspace search, active workspace selection, current role, and permission visibility.
- Dashboard is the first workspace-operations page after the user understands which workspace and permission scope they are operating in.
- The sidebar must stay focused on navigation plus current workspace context; it must not regain a workspace search/list/create surface.
- Future UI tickets should preserve this order: Account -> Dashboard/My Tasks -> Build -> Operate -> Evaluate -> Admin -> Settings.

## Design Review Decision: Canonical Interaction States

Approved during `/plan-design-review`: every major page must handle loading, empty, error, success, and partial states with consistent user-facing language.

| Surface | Loading | Empty | Error | Success | Partial |
|---|---|---|---|---|---|
| Account | Show stable account/workspace skeleton and reserved status area. | Explain that the user has no workspace yet and make Create workspace the primary action. | Show inline account/workspace load failure with Retry; keep logout available. | Show identity, current workspace, workspace list, role, permissions, and management actions. | Show loaded identity with workspace or permission sections marked unavailable instead of hiding the whole page. |
| Dashboard | Show workspace status skeleton and disabled action shortcuts. | Explain which capability is missing first and link to the right setup page. | Show dashboard load failure with Retry and keep sidebar navigation usable. | Show readiness, next action, attention queue, permissions, and platform coverage. | Show available metrics while marking missing data sources as unavailable or not configured. |
| Data | Show import/folder/list skeletons without shifting form controls. | Explain no datasets exist and make Import dataset primary. | Show import/list failure near the affected section. | Show folders, searchable dataset list, examples, labels, and delete/move controls by permission. | Show dataset list even if example loading fails; isolate the failed panel. |
| Knowledge | Show upload/folder/document/chunk skeletons without moving focused fields. | Explain no knowledge exists and make Upload document primary. | Show upload/index/list/chunk failure in the relevant section. | Show folders, documents, chunks, status, move/delete/reindex actions, and citations context. | Show document library even if chunks or embeddings are still indexing. |
| Agents | Show agent picker/runtime skeleton and disable run controls until config loads. | Explain no agents exist and make Create agent primary for permitted users. | Show agent config/run failure near the relevant action. | Show active agent, runtime controls, model route, recent runs, and run form. | Show agent metadata even if summaries, model routes, or recent runs fail. |
| Runs & traces | Show run list and trace skeletons separately. | Explain no runs exist and link to Agents. | Show trace load failure without clearing run history. | Show graph steps, model calls, tools, guardrails, costs, citations, checkpoints, and review links. | Show loaded trace sections and mark missing spans/model calls/tool calls individually. |
| Human review | Show queue skeleton and keep resolved history separate. | Explain no pending reviews and show recent resolved reviews if available. | Show claim/resolve/load failure near the affected review. | Show pending queue, selected case, evidence, proposed answer, decision editor, and history. | Show selected review with missing trace/evidence marked unavailable. |
| Evaluations | Show run list/results skeletons separately. | Explain no evaluations exist and make Run evaluation primary. | Show evaluation run/list/detail failure in place. | Show per-language metrics, baseline comparison, result evidence, and trace links. | Show completed result cards while marking failed modes or missing graph-run traces. |
| Usage & costs | Show summary and ledger skeletons separately. | Explain no AI runs exist and link to Agents/Evaluations. | Show cost summary or ledger failure in place. | Show total cost, tokens, latency, purpose/model breakdowns, and recent AI runs. | Show summary even if ledger page or filters fail. |
| Admin pages | Show page-specific skeleton and disabled mutations until permission context loads. | Explain what resource is not configured yet and identify the primary setup action. | Show permission/configuration failure with exact next step. | Show role-aware controls, auditability, and lifecycle actions. | Show readable configuration while marking restricted or unavailable mutations clearly. |

State rules:
- A state message must describe what the user can do next, not backend internals.
- Errors must preserve navigation and any already loaded data.
- Partial states should be visible and labeled; never replace the entire page with a generic failure when only one panel failed.
- Loading and status messages must reserve space so create/edit actions do not make the page jump.

## Design Review Decision: User Journey Storyboard

Approved during `/plan-design-review`: the app must feel like a guided professional AI operations workflow, not a collection of admin pages.

| Step | User does | User should feel | Plan specifies |
|---|---|---|---|
| 1 | Opens the app and lands on Account | Oriented: I know who I am, which workspace I am in, and what I can do. | Account is first, with identity, workspace list, current role, permissions, and create/switch/manage actions. |
| 2 | Opens Dashboard/My Tasks | Directed: I know the next operational action instead of guessing where to start. | Dashboard shows readiness and coverage; My Tasks shows backend-ranked attention items with action targets. |
| 3 | Adds Data and Knowledge | In control: I can curate examples and evidence before involving the agent. | Data and Knowledge use folders, bounded lists, search, upload/import, move/delete, and clear empty states. |
| 4 | Configures and runs an Agent | Confident but guarded: this is an inspectable workflow, not a free-form chatbot. | Agents page exposes runtime controls, model route, token budget, run action, and route to trace. |
| 5 | Opens Runs & traces | Trust-building: I can see why the system acted and what evidence/model/tool was used. | Trace page shows graph steps, retrieval, context packing, guardrails, model calls, costs, checkpoints, and review links. |
| 6 | Resolves Human review | Accountable: risky AI output does not silently ship. | Human review shows pending queue, selected case, evidence, proposed answer, decision editor, and history. |
| 7 | Runs Evaluations | Evidence-driven: quality is measured by language, mode, routing, citations, and baselines. | Evaluations show per-language metrics, baseline comparison, prompt evidence, and trace links. |
| 8 | Checks Usage & costs/Admin | Operationally mature: cost, permissions, model routes, prompts, system health, and audit are visible. | Usage/Admin pages show cost ledger, models, prompts, members, health, settings, and audit events with role-aware controls. |

Time-horizon design targets:
- 5 seconds: user understands Account -> Dashboard/My Tasks -> Build/Operate/Evaluate/Admin.
- 5 minutes: user can complete one demo path without asking what each page is for.
- 5 years/interview: user can explain workspace isolation, traceability, human review, evaluation, and token economy as product decisions.
## Design Review Decision: Visual System Hardening

Approved during /plan-design-review: future UI tickets must treat the visual system as a product contract, not incidental CSS.

Visual vocabulary rules:
- Typography: use a deliberate professional app font stack that supports English, Japanese, and Chinese. Prefer a named product font first, then CJK-aware fallbacks such as Noto Sans JP and Noto Sans SC, then system fallback only at the end.
- Color: keep the GitHub-like neutral base. Use semantic blue for navigation/focus/links, green for success/primary completion, yellow for warning/review, and red for danger/errors. Do not introduce decorative purple/blue gradients, blobs, or one-note palettes.
- Icons: prefer familiar lucide icons in future implementation tickets. Until an icon library is installed, use only obvious symbols with accessible labels; avoid ornamental or abstract symbols that require guessing.
- Layout: page sections flow top-to-bottom. Use grids only inside dense repeated sections such as metrics, cards, documents, traces, and permission summaries. Do not return to multi-column page-level workbenches.
- Surfaces: cards should represent concrete items, repeated resources, modals, or framed tools. Page sections should not become nested decorative cards.
- Copy: section headings and status messages must tell the user what the area is for and what action is possible. Avoid backend-internal labels in user-facing UI.
- Motion and status: create/edit/delete feedback must reserve space and avoid page shake, focus loss, or jump-to-top behavior.

Future implementation notes:
- Replace abstract sidebar tokens with an explicit icon policy when adding the icon dependency.
- Keep the sidebar as navigation plus current workspace context only; workspace creation and workspace list management remain on Account.
- Validate the visual system in browser QA, not only with TypeScript or build checks.

## Design Review Decision: Responsive And Accessibility QA Contract

Approved during /plan-design-review: broad UI tickets must verify responsive behavior and accessibility-sensitive interactions in the browser, not only through build/typecheck.

Required QA coverage for future UI implementation tickets:
- desktop and narrow/mobile viewport checks;
- page-level single-column flow with compact grids only inside repeated content;
- collapsed sidebar icon bounds and accessible names;
- visible keyboard focus through navigation, quick links, forms, pagination, and destructive actions;
- input focus stability while typing, creating, filtering, editing, and validating;
- placeholder hints remain placeholders and never become persisted real values;
- status messages reserve space, avoid page shake, and use temporary success feedback where appropriate;
- long workspace names, filenames, CJK text, IDs, and error messages do not clip controls or overlap content;
- growing lists remain bounded with pagination, search, filters, folders, or detail inspectors.

Future Playwright expansion should cover the regressions already found by manual review: focus loss, jump-to-top rendering, seeded placeholder values, sidebar clipping, page-level multi-column regressions, and unbounded lists.

## Design Review Decision: Decomposition Before More Broad UI Work

Approved during /plan-design-review: the next major implementation ticket should reduce frontend coupling before additional broad UI polish or feature work.

Current risk evidence:
- frontend/src/app/AppShell.tsx is over 8,000 lines and mixes layout, navigation, API orchestration, state, rendering, and page behavior.
- Several page components already exceed the repository size guidance, especially Agents, Documents, Overview, Prompts, Data, Tools, and Models.
- Backend files such as support_agent_graph.py, agent_service.py, agents.py, and evaluation_runner.py also need later decomposition, but frontend decomposition is the immediate UX-risk reducer.

Decision:
- Make the next implementation ticket a focused frontend architecture decomposition pass.
- Preserve current behavior and visual direction first; do not combine decomposition with redesign or new features.
- Split responsibilities into layout/navigation, API client, shared hooks/state, page containers, and smaller page-specific components.
- Keep browser smoke coverage for account/workspace, sidebar, data, knowledge, agent run, human review, evaluation, and costs.
- Create a separate later backend decomposition ticket for LangGraph runtime, agent service, and agent routes.

## Non-goals
- No backend API changes.
- No new first-class tool registry or guardrail configuration page.
- No route restructuring or deep frontend state refactor.
- No visual redesign beyond IA labeling and small navigation token styling.

## Validation
Run from the repository root:

```bash
cd frontend
npm run test
npm run build
```

Then rebuild and smoke check the local app:

```bash
docker compose up -d --build frontend
curl -sS http://127.0.0.1:8000/health
curl -sS -I http://127.0.0.1:5173
```

## Human Review Checklist
- Confirm the sidebar no longer feels like a numbered tutorial path.
- Confirm page names match the platform mental model.
- Confirm Tools and Guardrails are described honestly and not presented as complete registries.
- Confirm a first-time technical user can infer the main workflow from the dashboard.
- Confirm the existing demo workflow still works from the browser.

## Risks
- The app still uses a single-page tab layout, so URLs do not yet reflect the new IA.
- Tool and guardrail management are still runtime-observability surfaces, not full admin resources.
- Dashboard readiness remains a checklist, but it now represents platform capabilities rather than a numbered demo.

## Interview Notes
Explain that the IA was intentionally changed from a demo walkthrough to a platform console: Build configures data, knowledge, agents, prompts, and models; Operate inspects runs and human review; Evaluate measures quality and spend; Admin governs auditability. Also explain the honest MVP boundary: tool calls and guardrails are traceable today, while first-class registries are future tickets.
