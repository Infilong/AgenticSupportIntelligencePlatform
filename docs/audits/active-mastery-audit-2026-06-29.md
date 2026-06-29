# Active Platform Audit Report: Frontend/Backend Polishment

Date: 2026-06-29  
Scope: `/home/infilong/project/AgenticSupportIntelligencePlatform`

Status source references:
- `frontend/src/app/AppShell.tsx`
- `frontend/src/pages/*`
- `backend/app/*`
- `docs/*`
- `npm run -C frontend build`

## 1) Current Product Assessment
Backend is substantially implemented as a real multilingual AI platform:
- Auth/workspace/membership model with role checks
- Dataset import + label support for English/Japanese/Chinese
- Knowledge ingestion + chunking + vector retrieval + citations
- LangChain abstractions and LangGraph workflow orchestration
- Guardrails, human review routing, model-call accounting, traceability, cost summary, audit logs

Frontend has meaningful functional breadth but is not yet organized as a professional console by architecture quality:
- One file still drives most orchestration (`frontend/src/app/AppShell.tsx`: 8,623 lines)
- Only part of the page ecosystem is cleanly split into component modules
- Build currently fails from extraction mistakes in migrated page files.

## 2) What feels toy-like now
- Workflow is powerful but visually dense and hard to parse.
- Action order is not yet communicated as a mandatory operations sequence.
- Some core tasks feel "feature inventory" rather than guided operations.

## 3) What is confusing now
- New users cannot infer next action from first view.
- Multiple advanced operations are mixed with setup flows.
- Role context exists but is not always used as workflow framing.
- Page extraction is incomplete, leaving technical debt visible.

## 4) What does not match professional style
- Inconsistent page rhythm and state patterns.
- Dense shell-level responsibilities in `AppShell` create fragility.
- Build-blocking UI extraction issues signal an incomplete architecture transition.

## 5) Navigation / sidebar problems
- Sidebar exists but currently emphasizes tabs rather than a workflow-first operations map.
- Feature visibility is grouped but not fully stable by role intent.
- Collapsed/expanded behavior needs to enforce role/path clarity with stronger active-state affordances.

## 6) Missing permission-aware UX
- Backend permission checks are present and used; frontend UX still needs role-first defaults.
- Destructive and admin-level actions should appear as gated by role, with explicit rationale.

## 7) Missing task / attention workflow
- Backend attention data exists, but “what I should do now” is not the dominant surface.
- Review/trace/cost actions are available but not arranged as a strict operating loop.

## 8) Missing backend support for professional UI
- Core product surfaces are available in backend APIs and models.
- For polished first-run workflow, need better backend summary endpoints to reduce client-side orchestration.

## 9) Data/tool organization problems
- Folders for datasets and documents are present, but list-heavy surfaces still feel list-first, not operations-first.
- Tool/guardrail governance is visible in traces but not fully first-class as navigable catalog products.

## 10) UI/UX gaps
- Shared primitives and error/loading states are inconsistent across pages.
- Not all high-signal pages are route-like modules with standardized composition.
- Review state and evidence flow are operationally present but visually under-prioritized.

## 11) Backend/data-model gaps
- No immediate blocking gaps for current frontend recovery.
- Useful near-term additions:
  - stronger run-route->trace/span metadata for cross-page drilldown UX
  - richer `AgentConfig` metadata (`owner`, `description`, `use_case`) for catalog UX
  - clearer audit linkage for folder/move/archive lifecycle actions

## 12) Agent workflow gaps
- Graph workflow logic exists, but end-to-end product story should be rendered as:
  input → evidence retrieval → policy/checks → routing → answer/cost → review → trace.
- Tool and policy surfaces need first-class pages and summaries.

## 13) Traceability gaps
- Trace and guardrail data are implemented.
- Need standardized trace navigator and dashboard entry points that explain decisions as first-class operations.

## 14) Guardrail/governance gaps
- Guardrails are present; governance UI is still secondary.
- Need policy intent pages with reason, severity, action and remediation.

## 15) Evaluation gaps
- Evaluations exist by JSONL suite/case flow and metric outputs.
- Need clearer suite-level organization and regression posture at dashboard level.

## 16) Cost/token observability gaps
- Token, cost and latency data exist.
- Outlier signaling, model-level comparisons, and budget-risk actioning are not yet the default view.

## 17) Admin / developer experience gaps
- Backend has role scope but frontend still mixes admin/developer/reviewer paths.
- Settings and operations surfaces need explicit role pathways.

## 18) Best-practice findings (applied/relevant)
- React architecture: split large modules into typed components and stable prop boundaries.
  - https://react.dev/learn/thinking-in-react
- FastAPI: domain routers/services + explicit dependency-based authorization.
  - https://fastapi.tiangolo.com/tutorial/bigger-applications/
  - https://fastapi.tiangolo.com/tutorial/dependencies/
- Authorization/least-privilege from backend-to-UI.
  - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- Accessibility and contrast.
  - https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
  - https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- Sidebar and navigation hierarchy guidance for grouped destination-first layouts.
  - Material Design drawer/navigation guidance
- Observability model for traces/spans.
  - https://opentelemetry.io/docs/concepts/signals/traces/

## 19) Recommended information architecture
- Overview
- Build: data, knowledge, agents, tools, guardrails
- Operate: runs, traces, reviews
- Evaluate: evaluation suites, runs, comparisons
- Costs: budget, latency, model cost posture
- Admin: workspace, members, prompts, models, audit, system

## 20) Recommended sidebar structure
- Collapsible left nav with two states: expanded labels and compact mode.
- Workspace + role is always visible.
- High-frequency quick links on top:
  - Overview, My tasks, Active reviews, Last run trace, High-cost runs
- Permission-aware visibility (hide disabled actions rather than rendering broken UI).

## 21) Recommended dashboard plan
- Top section: workspace, role, permission summary.
- Middle: attention queue (pending review, failed/high-cost runs, indexing errors).
- Lower: recent traces, latest evaluation status, cost posture.
- Each card: what happened + impact + next action + direct jump destination.

## 22) Role/permission-aware UX plan
- Owner/admin: default entry to members/workspace/policies/cost/audit controls.
- Developer: default entry to agents/tools/traces/evaluation/cost reliability.
- Reviewer: default entry to review queue + evidence + citations + answer edits.
- Viewer: read-only insight surfaces + clear restriction explanation.

## 23) Agent / Tool / Guardrail / Evaluation / Cost page plan
- Agents: catalog, metrics, recent failures, run history links, model policy.
- Tools: catalog, schema, run history, permission profile.
- Guardrails: policy list, policy runs, severity outcomes, route effects.
- Evaluations: per-language and baseline comparison, failed-case drilldown.
- Costs: workspace/agent/run/model summaries, outliers, budget posture.

## 24) Backend/API gap list
- Add/strengthen summary endpoints for:
  - dashboard attention cards by role
  - workflow jump targets
  - high-cost/failure hotspots
  - trace summary cards for quick navigation
- Preserve backward compatibility; do not delay UI recovery by introducing API debt.

## 25) Database/model gap list
- Add lifecycle metadata as needed on mutable resources (`archived`, `archived_by`).
- Keep workspace + folder indexes current; add stronger cross-resource dashboard indexes as needed.
- No blocking schema change for immediate UX-0 recovery.

## 26) Prioritized implementation roadmap
### Phase 1 (stability first)
1. Repair page extraction build blockers in `OverviewPage`, `DocumentsPage`, and any migrated page.
2. Finish route-like wiring for existing pages and standardize panel patterns.
3. Keep backend behavior unchanged while reducing shell ownership.
4. Add deterministic browser smoke checks for overview → review → trace.

### Phase 2 (professional structure)
1. Introduce shared primitives (`PageHeader`, `SectionPanel`, `WorkflowCard`, `StatusBanner`).
2. Convert Overview/Tasks to explicit attention-first workflow.
3. Add explicit role/action ribbon and quick-links.
4. Standardize load/error/no-permission states across pages.

### Phase 3 (mature platform UX)
1. Route-level navigation migration (React Router) after module stability.
2. Expand backend summary API support for role-scoped attention cards.
3. Advance governance catalogs (tool/guardrail) and policy lifecycle UX.

## 27) Phase 1 quick wins
- Fix `AppShell.tsx` and page extraction compile integrity.
- Make role/context and "what to do next" visible in Overview.
- Make review/trace/cost high-signal cards action-linked.
- Keep changes confined to shell/page composition and shared primitives.

## 28) Phase 2 structural improvements
- Shared component library growth by page type.
- Consistent permissions messaging and disabled-state explanations.
- Pagination/search/filter with stable folder paths on data-heavy resources.
- Workflow trace links from attention cards to run detail.

## 29) Phase 3 advanced features
- OpenTelemetry-grade trace IDs in UI context.
- Enterprise RBAC/ABAC extension.
- Additional scale-ready deployment and observability layers.

## 30) Risks if UI is improved before backend alignment
- Professional look without strong role-aware controls weakens credibility.
- Action ambiguity remains if backend summaries are inferred rather than supported.
- Monolithic shell + partial extraction increases maintenance/review risk.

## Severity-ranked gap list
- **P0**
  1. `frontend/src/app/AppShell.tsx` remains monolithic (8,623 lines).
  2. Page extraction currently breaks build:
     - `frontend/src/pages/OverviewPage.tsx` has `const primaryAction` syntax break
     - `frontend/src/pages/DocumentsPage.tsx` has unclosed `<aside>`
  3. Workflow-first entry path is not enforced in first-view.
- **P1**
  1. Permission/routing clarity and role path defaults need stronger UX framing.
  2. Dashboard does not yet prioritize attention actions as default flow.
  3. Trace and review actionability requires clearer route architecture.
- **P2**
  1. Visual tone/spacing consistency across pages.
  2. Shared componentization and reusable patterns incomplete.
- **P3**
  1. Full cloud observability, ABAC/enterprise RBAC, OpenTelemetry export.

## Current evidence snapshot
- `npm run -C frontend build` fails:
  - `frontend/src/pages/OverviewPage.tsx(125,48)` syntax issue
  - `frontend/src/pages/DocumentsPage.tsx(327,11)` missing closing tag
- Frontend file status:
  - `AppShell.tsx`: 8,623 lines
  - `OverviewPage.tsx`: 398 lines
  - `DocumentsPage.tsx`: 436 lines
  - `DatasetsPage.tsx`: 371 lines
- Extracted pages exist for `Overview`, `Tasks`, `Members`, `Audit`, `Datasets`, `Documents`.
- Shell currently imports only those modules plus many inline handlers.

## First 5 implementation tickets (post-audit gate)

### Ticket 1 — UX-0A: Stabilize shell-page extraction without behavior change (blocking)
**Scope**
- Fix page extraction compile breakages and remove migrated page render logic from `AppShell` sections.
**Acceptance**
- Frontend build passes.
- Existing user behaviors are preserved.

### Ticket 2 — UX-0B: Shared page layout primitives
**Scope**
- Add shared primitives (`PageHeader`, `SectionPanel`, `StatusBanner`, `WorkflowStep`).
- Standardize empty/loading/error/permission visuals.

### Ticket 3 — UX-1: Overview-first workflow
**Scope**
- Make overview explicit: workspace context, role, permission posture, attention queue, direct action links.

### Ticket 4 — UX-2: Role-aware navigation and data/knowledge organization
**Scope**
- Collapsible sidebar with explicit route-like workflow groups.
- Strong role-based visibility and clear disabled explanations.
- Folder + list controls consistency for Datasets/Knowledge.

### Ticket 5 — UX-3: Trace/Review/Cost integration
**Scope**
- Unify actions from attention cards into trace review, human review, and cost drill-down paths.
- Ensure one-click transition between overview card and corresponding resource pages.
