# Frontend & Backend Polishment Audit (Pre-Implementation)

Date: 2026-06-29
Objective: transform the current app from a demo-like prototype into a professional, role-aware AI platform console.

## 1) Current product assessment

The platform now has strong backend platform substance:
- real workspace auth and membership, role membership endpoints, permission-based route gates
- LangGraph/LLM run execution with graph traces, tool calls, retrieval traces, guardrail results
- AI run ledger, evaluation runs, cost summaries, audit logs
- resource folder support for datasets/knowledge/agents/evaluations

Frontend now has structural improvement in progress: `App.tsx` is split and delegates most logic to `app/AppShell.tsx`. However the shell remains very large and mixes UI state, API orchestration, rendering, and validation.

## 2) What feels toy-like now

- Workflow does not read as a production console first; users must infer steps.
- Dashboard is rich but not yet framed as a clear 1st-run operating sequence.
- Many high-signal concepts (trace, review, cost) are present, but page composition is still dense.
- Styling has improved in parts but lacks a consistent, disciplined page shell hierarchy expected in professional admin consoles.

## 3) What is confusing in current layout

- Sidebar and content are present, but one-file concentration causes long scans and unstable maintenance.
- Page switching is active-tab-based but not surfaced as a workflow first view with “what to do now”.
- Review and run actions are available but decision flow is not visually guided from queue → action → outcome.
- Multiple large sections inside one screen cause context overload on smaller viewports.

## 4) Black-and-white professional mismatch

- The app is close to a usable console, but still not using a strict design system.
- Status hierarchy is present but not consistently encoded through shared primitives and page-level patterns.
- Typography/spacing/section scaffolding varies across panels, making it look like different authorship.

## 5) Navigation/sidebar issues

- Sidebar has tabs and grouping but still behaves as feature navigation before workflow navigation.
- Role-based filtering is implemented in logic but the visual hierarchy and collapsed/expanded behavior should be more deliberate.
- Sidebar state must become a stable orientation system: current route obvious, collapsed mode predictable, quick jump links always available.

## 6) Missing permission-aware UX

- Permissions exist in UI and backend, and backend enforcement is generally present.
- UX does not yet consistently provide role-based entry paths (reviewer/developer/admin first-view priorities).
- Permission failure messaging exists but does not yet form a guided user journey.

## 7) Missing task/attention workflow

- Attention data exists and can be read from API/state, but queue-to-action flow is not yet a first-class, step-led experience.
- Priority queue exists, but it is not yet embedded as a persistent “what should I do next” operating path.

## 8) Missing backend support for professional UI

The backend supports most required operational data and controls, including:
- workspace, permissions, runs, traces, reviews, evaluations, cost summary, audit logs
- folder and archive states on major resources

Risks remain:
- Large domain services (`backend/app/services/agents.py`, `support_agent_graph.py`, `api/v1/agents.py`) still carry multiple responsibilities.
- Some observability surfaces are data-complete but not optimized for role-specific UI summaries.

## 9) Data/tool organization problems

- Folder-based organization exists, but tool page flow is still embedded in one shell and not broken into role-aware modules.
- Data and knowledge need clearer vertical workflows (ingest → organize → validate → run).

## 10) UI/UX gaps

- No unified route-like page components yet for dashboard, agent, trace, evaluation, cost, and settings areas.
- Empty/loading/error states are present but not standardized across all sections.
- There is no shared design token layer and consistent section primitives.

## 11) Backend/data-model gaps

From current state, no migration is required for UX-0 structural work, but future product-credibility work likely needs:
- richer `AgentConfig` metadata for ownership/description/intent/use-case fields
- stronger dashboard summary denormalization for faster front-page role-aware cards
- clearer normalized span/trace linking metadata for future cross-page drill-down

## 12) Agent workflow gaps

- Agent configuration, runs, and workflow introspection exist but are spread in shell rendering logic.
- Page-level workflow structure (prepare → run → inspect → remediate) is not yet explicit.

## 13) Traceability gaps

- Traces are rich and real (steps, calls, costs, guardrails, checkpoints).
- Traceability is not yet the dominant first-class onboarding experience from dashboard to page-level remediation.

## 14) Guardrail/governance gaps

- Guardrail actions exist, but page treatment still presents as diagnostics rather than governance controls with clear policy intent.
- Routing/rule outcomes should be tied with next action and related graph run.

## 15) Evaluation gaps

- Evaluation suite/run/compare capabilities exist.
- UI still needs clearer language-first quality signals and “regression now” recommendations.

## 16) Cost/token observability gaps

- Cost summaries are implemented.
- Product-level clarity needs improvement for: high-cost outliers, p50/p95/p99 latency context, agent-level spend posture, and failure-cost correlation.

## 17) Admin/developer experience gaps

- Admin and developer actions are available but mixed with general dashboard layout; user path is not role-first yet.
- Settings areas need clearer separation and permission-tier defaults.

## 18) Recommended information architecture

```text
Platform
├── Overview
│   ├── Dashboard
│   └── My Tasks
├── Build
│   ├── Data
│   ├── Knowledge
│   ├── Agents
│   ├── Tools
│   └── Guardrails
├── Operate
│   ├── Runs
│   ├── Traces
│   └── Human Review
├── Evaluate
│   ├── Evaluation Suites
│   ├── Evaluation Runs
│   └── Usage / Costs
└── Admin
    ├── Members
    ├── Prompts
    ├── Models
    ├── Audit
    ├── Workspace Settings
    └── System Health
```

## 19) Recommended sidebar plan

- Implement collapsible sidebar with two stable states (expanded/collapsed).
- Keep page groups fixed and role-filtered.
- Keep current tab obvious in both states.
- Keep quick-jump links for high-frequency tasks (tasks, active review, latest trace, high-cost alerts).

## 20) Recommended dashboard plan

- Show workspace context + role + permission summary at top.
- Add workflow action strip with recommended next step.
- Add attention board (reviews, failed runs, guardrail blocks, high-cost, stale indexing).
- Add recent traces/evaluations with action links.
- Add quick links to role-specific areas.

## 21) Role/permission-aware UX plan

- **Reviewer:** priority view around review queue, answer evidence, citations, approvals.
- **Developer:** priority for agent config, traces, tools, guardrails, evals.
- **Admin:** member/workspace controls, budgets, providers, audit, policy config.
- **Viewer:** read-only observability plus clear lock-state explanation where access is restricted.

Backend must remain source of truth; frontend should only optimize clarity.

## 22) Agent/Tool/Guardrail/Evaluation/Cost page plan

### Agents
- Page split: catalog, active agent context, workflow controls, recent runs, summary metrics.

### Tools
- Tool catalog + usage history + schema/permission visibility + recent failures.

### Guardrails
- Policy catalog + severity/action + result history + policy links.

### Evaluations
- Run list + baseline comparisons + language/regression view + trace links + case-level detail.

### Costs
- Workspace/agent/tool/purpose/cost posture and budget-risk cards with remediation entry points.

## 23) Backend/API gap list

Current code indicates these practical UX-backed API needs:
- better server summary payloads for dashboard cards (to reduce client-side orchestration)
- additional dedicated endpoints for “next operational actions” by role
- stronger query filters where UI surfaces need bounded/ordered views
- stable trace-summary endpoint for quick dashboard drill-down
- no missing core APIs for existing core capabilities; remaining work is shape/consistency and modularization.

## 24) Database/model gap list

No new migrations required for current UX-0 work, but likely near-term additions:
- extended agent metadata fields (description, lifecycle intent)
- trace/span relation metadata improvement
- optional evaluation suite/domain metadata if suite-first UX is expanded

## 25) Best-practice findings (applied)

Where applicable and already reflected in this plan:
- Component/page ownership by responsibility (React guidance: split by concerns)
- FastAPI module boundaries and routers per domain
- OWASP least-privilege and server-side enforcement
- WCAG contrast/focus for high-contrast serious console design
- Span-like mental model for traces (step timeline + status + latency + errors)
- Stable drawer/navigation patterns for grouped nav with current-state visibility

## 26) Prioritized implementation roadmap

- **Phase 0 (stabilize)**: finish page/module extraction for all major tabs; isolate shared primitives.
- **Phase 1 (workflow + clarity)**: dashboard-first workflow, quick links, attention-first queue, role-based entry paths.
- **Phase 2 (structure)**: page-level componentization, route-like navigation (if needed), consistent design system.
- **Phase 3 (advanced)**: backend module splits, stronger trace/span model coherence, cloud-ready observability.

## 27) Phase 1 quick wins

1. Complete page module extraction for all major tab panels.
2. Introduce shared design tokens and section primitives.
3. Rebuild dashboard around role-aware next actions.
4. Add collapsible, permission-aware sidebar with current-route affordance.
5. Add browser smoke checks covering My Tasks → Reviews → Runs/Trace → Costs.

## 28) Phase 2 structural improvements

1. Refactor service/API files into smaller responsibility modules.
2. Standardize empty/loading/error states.
3. Build trace run summary cards tied to graph node evidence.
4. Improve evaluation baseline + regression explanation UX.
5. Add role-based quick entry pages for admin/dev/reviewer.

## 29) Phase 3 advanced platform features

1. Real route system (React Router) after page modules are stable.
2. Stronger model/span trace export and observability mapping.
3. Provider secret/config lifecycle for production readiness.
4. Audit + policy settings as dedicated workflows.
5. Expanded scale-path features (warehouse/Cloud)

## 30) Risk if we only improve UI without backend support

- Looks professional but undermines credibility when users discover missing controls, inconsistent scope enforcement, or hidden policy/rule coupling.
- Hard to maintain because the frontend still concentrates logic and side effects in one shell file.
- Future feature velocity drops as new areas are appended to the same large module.

---

## Severity-ranked gap list

### P0 (critical for professional credibility)
1. Frontend remains a monolithic implementation (`app/AppShell.tsx` is 9,081 lines): hard to audit and hard to onboard.
2. No clean route-like page architecture across all tabs yet.
3. Lack of workflow-first first screen (tasks → action → outcome) in production posture.
4. Large agent/graph service modules still need modular split for long-term staff-level maintainability.

### P1 (important)
1. Sidebar/left navigation still requires workflow polish and stronger collapsed-state stability.
2. Dashboard is data-rich but not decision-first.
3. Permission-first role narratives are not yet explicit.
4. Page-level consistency and shared components incomplete.

### P2 (polish)
1. Visual design tokens and status hierarchy need finalization.
2. Traces/guardrails/evals/costs are strong but need narrative framing.
3. Standardized empty/loading/error variants needed across all pages.

### P3 (future)
1. OpenTelemetry export and enterprise RBAC extensions.
2. Full real-router migration with deep linking and shareable workflow URLs.
3. Secret/provider lifecycle maturity beyond local demo posture.

## First 5 implementation tickets (post-audit)

### 1) UX-0B: Shared UI primitives + page-level split continuation
- Goal: keep behavior unchanged while moving all major tab UIs into `frontend/src/pages/*` and shared UI parts into `frontend/src/app/*` + `frontend/src/components/*`.
- Files: split `frontend/src/app/AppShell.tsx`, add shared primitive/page scaffold modules.
- Tests: `npm run build`, `npm run test`, smoke run-through.
- Risk: prop churn and accidental regression during extraction.

### 2) UX-1: Professional shell and navigation
- Goal: introduce a consistent console shell with collapsible sidebar, quick links, role ribbon, and workflow-first page context.
- Files: `frontend/src/app/*`, `frontend/src/pages/*`, `frontend/src/styles.css` and split CSS tokens.
- Risk: visual churn without action clarity.

### 3) UX-2: Attention-first workflow dashboard
- Goal: reframe Overview into a clear “what to do next” panel with role-aware priorities.
- Files: new `DashboardPage.tsx`, shared workflow/priority components.
- Risk: overemphasis on volume over action.

### 4) UX-3: Data/Knowledge workflow pages
- Goal: explicit vertical workflows: import/upload → folders → validate → inspect readiness.
- Files: `DataPage.tsx`, `KnowledgePage.tsx`, folder controls.
- Risk: hidden state if async workflows are not surfaced as status.

### 5) BE-0A: Backend service modularization for agent graph area
- Goal: split `support_agent_graph.py` / `agent_service.py` / `api/v1/agents.py` into clear modules.
- Files: backend service/router split with equivalent behavior.
- Tests: targeted backend tests (`tests/test_agents.py`, `test_langchain_support.py`, `test_human_reviews.py`, `test_ai_observability.py`, then full backend test suite).
- Risk: introducing import cycles and changing transactional boundaries.
