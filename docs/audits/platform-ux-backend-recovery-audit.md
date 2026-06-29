# Platform UX & Backend Recovery Audit

Date: 2026-06-29  
Objective: transform the current product into a professional, serious AI agent platform UI/backend recovery milestone before any UX implementation.

## 1) Current Product Assessment
The platform already has substantial backend product depth:
- workspace, auth, role-permission boundaries
- dataset import and multilingual labeling
- knowledge doc upload/chunking/versioning
- LangChain tool/model abstraction usage
- LangGraph stateful runs with graph steps, checkpoints, tool calls
- AI run ledger (provider/model/tokens/latency/cost)
- human review routing and states
- retrieval traces, guardrails, evaluations, audit logs, system health

Frontend has made progress but remains unstable operationally for a serious portfolio: `frontend/src/app/AppShell.tsx` is a 8,623-line god component, so the app is structurally difficult to reason about despite functional coverage.

## 2) What Feels Toy-Like Now
- Product narrative is not obvious by first glance.
- Dense section-by-section layouts reduce clarity on what to do next.
- Multiple controls are present without explicit next-action sequencing.
- Some pages read as engineering demos (raw sections) rather than a guided operations console.

## 3) What Is Confusing in Current Layout
- One very large shell owns state management, API orchestration, rendering, and validation.
- High-signal actions (reviews, failed runs, cost risk) are not always surfaced as top priorities.
- Review and policy outcomes are present but not first-class operational tasks.
- Layout rhythm shifts too often between different page-like blocks.

## 4) What Does Not Match Professional Style
- The visual style is partly updated but still inconsistent by section.
- No full, predictable page hierarchy across core domains.
- Semantic hierarchy (workspace health, permission context, next action) is fragmented.
- Advanced details are too often mixed with default path.

## 5) Navigation / Sidebar Problems
- Sidebar is present but does not yet feel like a stable operations map.
- Current navigation still emphasizes feature inventory, not operational workflow.
- Collapsed/expanded behavior is not yet authoritative for first-run understanding.
- Feature visibility is not strongly role-hardened in the nav UX.

## 6) Missing Permission-Aware UX
- Backend has permission machinery; frontend currently lacks consistently visible role-first journeys.
- Some action visibility and disabled behavior lacks “why” messaging tied to workspace policy.
- Role entry paths (reviewer/developer/admin/viewer) are not always explicit on arrival.

## 7) Missing Task/Attention Workflow
- Attention APIs exist, but “what needs action now” is not a dominant entry path.
- Trace → review → resolution flow is present, but not framed as workflow defaults.
- No single page-level attention contract tying severity + recommended action.

## 8) Missing Backend Support for Professional UI
- Core primitives are present and trustworthy for current scope.
- Missing backend payload shaping for role-aware summary cards currently pushes logic to UI composition.
- List/filter/sort ergonomics can be better aligned with future UI scale and folder views.

## 9) Data / Tool Organization Problems
- Foldering exists in parts but growth control patterns are inconsistent by resource.
- Data/knowledge/admin/dev/ops views are too coupled in one rendering surface.
- Tool and guardrail management are trace-rich but not yet first-class catalog surfaces.

## 10) UI / UX Gaps
- No fully consistent scaffold for empty/loading/error/permission states.
- Repeated layout idioms differ across pages.
- No shared architecture of page composition yet (layout primitive + route-like page modules).
- Missing clear decision-first copy in core views.

## 11) Backend / Data-Model Gaps
- No migration blocker for today’s structural frontend recovery.
- Near-term schema improvements likely useful:
  - richer `AgentConfig` metadata (owner/context/use intent)
  - stronger run-to-trace/spans metadata for cleaner cross-page drill-down
  - optional lifecycle fields for major resources (archive/deactivate)

## 12) Agent Workflow Gaps
- Agent runtime exists and is real.
- Product surface does not present the workflow lifecycle as a continuous journey (input → retrieval → decision → review/finalize).
- Config/operation/evidence views need clearer separation.

## 13) Traceability Gaps
- Trace data is present and strong.
- Trace viewer should become the canonical proof path with stronger entry links and route-level summaries.
- Cross-page drill-down from dashboard/review into specific trace spans needs stronger UX conventions.

## 14) Guardrails and Governance Gaps
- Guardrail execution exists but not yet packaged as policy-first controls with audit-readable rationale.
- UI needs clearer action outcome for each policy check.
- Human-review routing reasons should be surfaced as first-class operational context.

## 15) Evaluation Gaps
- Evaluation runner exists, including baseline ideas.
- No suite/case organization for scalable curation beyond current model.
- Regression signaling is not yet default dashboard language.

## 16) Cost / Token Observability Gaps
- Token/cost ledger exists.
- Outlier-first visibility is weak; users need stronger high-cost + failed-run prioritization.
- P50/P95/P99 latency and model-level accountability are not consistently operationalized as “what should I do now?” signals.

## 17) Admin / Developer Experience Gaps
- Backend has strong foundation.
- Frontend has not yet separated admin/developer/reviewer flows by intention and permission intent.
- Settings and governance surfaces should be de-conflicted into explicit domains.

## 18) Recommended Information Architecture
```text
Overview
  - Workspace dashboard
  - My tasks
Build
  - Data
  - Knowledge
  - Agents
  - Tools
  - Guardrails
Operate
  - Runs / Traces
  - Human Review
Evaluate
  - Evaluations
  - Usage / Costs
Admin
  - Members
  - Prompts
  - Models
  - Audit Logs
  - Workspace / System settings
```

## 19) Recommended Sidebar Structure
- Implement permission-aware collapsible sidebar with two stable states.
- Keep expanded labels, collapsed compact tokens/icons.
- Top quick links for high frequency workflows:
  - Overview, My Tasks, Active Reviews, Latest Trace, High-Cost Runs
- Current page emphasis must remain obvious in both states.
- Hide unavailable features by role.

## 20) Recommended Dashboard Plan
- Workspace context panel: selected workspace, role, permission posture.
- Action strip: “recommended next action”.
- Attention queue: pending review, high-risk runs, failed runs, high latency/cost, indexing failures.
- Trace/result summary links: one-click drill-down.
- Cost and health cards with threshold-aware highlighting.
- Language-specific policy/compliance cards where relevant.

## 21) Role / Permission-Aware UX Plan
- **Owner/Admin:** members, budgets, provider controls, audit, policy and failure governance.
- **Developer:** agents, tools, runs/traces, guardrails, eval dashboards, model behavior debugging.
- **Reviewer:** pending review queue, citations, answer rationale, approved/edit/reject flow.
- **Viewer:** read-only clarity, status visibility, explicit restricted actions.

## 22) Agent / Tool / Guardrail / Evaluation / Cost Page Plan
### Agents
- Config catalog, recent runs, runtime controls, failure/routing stats, cost/latency summaries.

### Tools
- Tool registry with schema, usage policy, timeout/retry defaults, errors and related traces.

### Guardrails
- Policy list, severity/action, pass-fail history, trace and review linkage.

### Evaluations
- Suite/case management, per-language metrics, baseline comparison, trace-referenced failures.

### Costs
- Workspace/agent/model/run summary, latency percentiles, high-cost alerts, budget posture.

## 23) Backend / API Gap List
- Add/confirm API summaries for role-aware dashboard cards.
- Add/confirm bounded workspace attention endpoint (prioritized tasks by role).
- Ensure stable trace-summary endpoint with run->step->model/tool links.
- Ensure pagination/filter/sort consistency on large resource list surfaces.
- Add/delete/archive lifecycle endpoints for resource hygiene where operationally needed.

## 24) Database / Model Gap List
- No blocking migration needed for UX-0.
- Recommended future additions:
  - `folder_id` + hierarchy indexes for growth surfaces already in use
  - `archived_at`/`archived_by` on mutable resources that need lifecycle actions
  - explicit `owner_user_id` and richer metadata on `AgentConfig`
  - normalized trace-link metadata if cross-page drilldown UX scales further

## 25) Best-Practice Findings
- React: split by component responsibility and minimal state ownership for maintainability. Source: https://react.dev/learn/thinking-in-react
- FastAPI: domain routers/services and dependency layers scale maintainability. Source: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- OWASP AuthZ: server-side permission checks and least privilege are non-negotiable. Source: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- WCAG contrast/focus: justify monochrome high-contrast status design. Source: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html, https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- OpenTelemetry trace semantics: execution should be understandable via steps/spans with timing/status. Source: https://opentelemetry.io/docs/concepts/signals/traces/
- Material UI drawer guidance: grouped navigation with persistent current-location semantics.

## 26) Prioritized Roadmap
### Phase 1 (Stability + structure)
1. Finish and stabilize architecture cleanup (UX-0A/0B path): page modules + shared navigation + API client split.
2. Standardize dashboard/task-first flow and role-aware permission framing.
3. Ensure build/typecheck pass after each extraction step.
4. Add deterministic browser smoke path for key flows.

### Phase 2 (Product-grade presentation)
1. Professional black-and-white console redesign without visual clutter.
2. Promote trace/review/cost/evaluation workflows as actionable decision pages.
3. Role-specific landing pages and quick links.
4. Shared design component system for status, cards, tables, states.

### Phase 3 (Depth)
1. React Router migration after page layer is stable.
2. backend modularization and stronger summary endpoints.
3. Provider and policy management hardening.
4. Longer-term observability/export/ABAC extension.

## 27) Phase 1 Quick Wins
- Make `App.tsx` composition minimal (already partially done via `AppShell`).
- Complete page module extraction for all major areas.
- Standardize role-aware disabled actions and permission messaging.
- Add attention-first dashboard section with concrete action links.
- Create consistent state components (empty/loading/error).

## 28) Phase 2 Structural Improvements
- Refactor oversized backend files into smaller service/API units where behavior risk is highest.
- Add robust folder-bound UX for data/knowledge and long list controls.
- Build cross-page trace deep-link contracts.
- Add explicit review decision workflows and guardrail outcomes with remediation links.

## 29) Phase 3 Advanced Platform Features
- Real route-based navigation migration.
- Trace/span normalization and optional OpenTelemetry path.
- Tool and policy registries with richer metadata and lifecycle.
- Budget and rate-control operations and audit-ready policy templates.

## Severity-Ranked Gap List
- **P0 (critical for professional credibility):** monolithic `frontend/src/app/AppShell.tsx`; no route-like page composition for all domains; missing clear action-first dashboard.
- **P1 (important):** permission-aware navigation and role narrative not yet first-class; unstable consistency between pages and repeated section patterns.
- **P2 (polish):** design system consistency, standardized copy/states, cross-page visual rhythm.
- **P3 (future):** router migration, OTel export depth, enterprise RBAC/ABAC and provider secret lifecycle.

## First 5 Implementation Tickets

### Ticket 1 — UX-0A: Split AppShell Rendering into Page Modules (No Behavior Change)
**Goal:** complete page boundaries for existing tabs without changing behavior.  
**Acceptance:** no behavioral change, all routes working, build passes.

### Ticket 2 — UX-0B: Shared Application Layout Primitives
**Goal:** add stable `AppShell` composition with shared `PageHeader`, `SectionPanel`, `QuickLinks`, `StatusBanner`, `WorkflowStep`, `PermissionSummary`.

### Ticket 3 — UX-1: Workflow-First Dashboard
**Goal:** make “what is next” obvious and role-aware, based on tasks/attention.

### Ticket 4 — UX-2: Data & Knowledge Operational Pages
**Goal:** structure as foldered ingestion → organization → validation workflows with consistent CRUD actions.

### Ticket 5 — UX-3: Trace, Review, Evaluation, Cost Visibility Alignment
**Goal:** make trace-first operations easy to reach and actions explicit; connect dashboard cards to trace/review/eval/cost pages.

## Risks and Tradeoffs
- Doing visual redesign before extracting structure risks masking architectural debt.
- Keeping all logic in one shell impedes maintainability and interview-level defensibility.
- Over-splitting too early could add prop noise; target mechanical extraction with strict behavior parity first.
