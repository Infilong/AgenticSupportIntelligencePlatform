# Frontend & Backend Polishment Audit (2026-06-29)

Scope: `/home/infilong/project/AgenticSupportIntelligencePlatform`

This report is the active audit requested before any UX/architecture implementation ticket is approved.

## 1) Current Product Assessment
The platform has real AI backend substance already:
- Workspace, auth, membership, RBAC permissions.
- Dataset import + multilingual labeling + foldering.
- Knowledge upload/chunking/versioning.
- LangChain integrations and LangGraph workflow execution.
- Graph run/step traces, tool calls, guardrail checks, human review routing.
- AI run ledger, token accounting, budgets, costs, evaluations, and audit logs.

Frontend direction is materially ahead of early toy status, but it is still constrained by architecture concentration in one file and inconsistent page-level product orientation.

## 2) What Feels Toy-Like Now
- Many high-value workflows are present but surfaced as dense monolithic panels.
- User cannot immediately infer a default operational sequence on first login.
- Page boundaries are overloaded: navigation is present but task-orchestration narrative is weak.
- Some controls appear as long form lists before action guidance.

## 3) What Is Confusing in Current Layout
- Main shell is still in one very large component with mixed responsibilities.
- `frontend/src/pages` exists but only 4 of 17 required major functional areas are fully wired.
- Quick-start flow is present in copy, but not enforced by layout progression.
- Certain actions (e.g., deletion/move/refresh/resolution) are visible without consistent role-first framing.

## 4) What Does Not Match a Professional Admin Style
- Layout has promising structure, but the experience is uneven between sections.
- Some high-signal states (pending review, failed run, cost risk, indexing failure) are not consistently represented with a single decision hierarchy.
- Visual hierarchy still appears page-by-page ad hoc rather than a common console pattern.

## 5) Navigation / Sidebar Problems
- Collapsible sidebar exists and has state persistence in `localStorage`.
- Active label, role, and quick-links work, but:
  - not all high-priority workflow edges map to top-level navigation intent,
  - many tabs remain page functions in the shell instead of dedicated route-like components,
  - permission gating is present but not uniformly surfaced as task intent.

## 6) Missing Permission-Aware UX
- Backend permissions are mature:
  - `require_workspace_member`, `require_workspace_owner`, `require_workspace_permission` are implemented.
  - `permissions_for_role` defines role->permission mapping.
- Frontend should still expose these as first-class role narratives:
  - owner/developer/reviewer/viewer role entry points,
  - disabled actions need consistent explanations tied to backend permissions,
  - review/admin/developer paths should be explicit from Overview/Tasks.

## 7) Missing Task / Attention Workflow
- Attention endpoints and summaries exist in backend, and the shell has an attention model.
- The attention path is not yet the default “where to go next” engine in all major journeys.
- Task-to-page routing and completion evidence should be more deterministic.

## 8) Backend Support for Professional UI
Backend support is mostly sufficient for UX-0A.

Current gaps (for near-term workflow polish):
- Some frontend page groups are not yet split into reusable modules.
- Certain “go next” and “what changed” surfaces need cleaner backend summary endpoints for low-friction role dashboards.

## 9) Data / Tool Organization Problems
- Foldering support exists for knowledge and datasets.
- There is clear growth risk in flat, page-local list handling.
- The UI still mixes resource list, inspector, and action editing in monolithic page sections.

## 10) UI/UX Gaps
- No strict shared pattern for empty/loading/error/permission across all pages.
- Some section-level workflows are not consistent between Data/Knowledge/Tools/Guards/Agents/Trace.
- Several key operations are still difficult to discover by role intent.

## 11) Backend / Data-Model Gaps
- Not blocking for current UX-0, but improvements likely useful:
  - stronger cross-surface trace-link metadata (span-level semantics for UI drill-down),
  - more lifecycle fields for additional operations,
  - small dashboard summary envelopes to reduce overfetch.

## 12) Agent Workflow Gaps
- Runtime workflow exists and is instrumented, but user-facing explanation still needs workflow scaffolding:
  - run -> trace -> review -> evaluation -> cost result should be a single visible sequence.

## 13) Traceability Gaps
- Trace infrastructure exists and includes rich model/step data.
- The trace should be top-priority landing when operating tasks are open.
- Tool + guardrail + cost links should be standardized from one trace navigator.

## 14) Guardrail / Governance Gaps
- Guardrails and decision outputs are available.
- The governance map should be presented as first-class policy/action/state instead of only mixed within trace details.

## 15) Evaluation Gaps
- Evaluations are run and measured.
- Regression narrative and language-specific prioritization should be more visible in a dedicated dashboard-first flow.

## 16) Cost / Token Observability Gaps
- Cost accounting and ledger data are present.
- High-cost/failing run outlier signaling and next action suggestions are not universal.

## 17) Admin / Developer Experience Gaps
- Backend role enforcement and workspace policy are strong.
- UX still blends admin and ops flows and does not yet default each role to their highest value entry points.

## 18) Recommended Information Architecture
1. Overview
2. My Tasks
3. Agents
4. Data
5. Knowledge
6. Tools
7. Guardrails
8. Runs / Traces
9. Human Review
10. Evaluations
11. Costs / Usage
12. Admin
13. Settings
14. System Health

## 19) Recommended Sidebar Plan
- Keep collapsible sidebar with stable current-page indicator.
- Keep token/label mode (expanded/collapsed) with stable width behavior.
- Add role-labeled quick links near top for first actions:
  - Overview, Tasks, Reviews, Trace, Costs.
- Hide unavailable tabs and show disabled-but-visible items with rationale.

## 20) Recommended Dashboard Plan
- Dashboard should answer:
  - What is happening now?
  - Why does it matter?
  - What should I do now?
- Sections:
  - Workspace + role summary,
  - Ready checklist,
  - Attention queue (critical/high first),
  - Recent failed/risky events,
  - Trace/error entry,
  - Review queue,
  - Cost anomalies,
  - Health summary.

## 21) Role / Permission-aware UX Plan
- **Owner/Admin**: members, budgets, providers/models, audit, destructive actions.
- **Developer**: agents, tools, prompts, guardrails, traces, evaluations, cost/correlation.
- **Reviewer**: pending reviews, evidence, citations, route decisions.
- **Viewer**: read-only inspection with no destructive controls.

## 22) Agent / Tool / Guardrail / Evaluation / Cost Page Plan
### Agents
- Config, runtime health, recent run summary, route decision trend, cost and latency summary.

### Tools
- Catalog + schema + usage + failure + ownership + timeout/retry policy.

### Guardrails
- Policy registry -> execution result -> failure action -> trace link.

### Evaluations
- Suite/case-level view + baseline comparison + regression and language grouping.

### Costs
- Workspace/agent/model/run summaries with outlier alerts and review actions.

## 23) Backend/API Gap List
- No blocker for UX-0A.
- Useful additions:
  - endpoint for workspace-level role-aware summary panels (for dashboard cards),
  - stable short task payload with route targets,
  - stable trace linkage IDs where needed for cross-page drilldowns,
  - explicit pagination consistency across more list endpoints (if not already).

## 24) Database/Model Gap List
- Already supports current surfaces.
- Potential next-schema work:
  - extra lifecycle flags/indices for additional resources if front-end grows,
  - stronger run-route-to-policy/trace join metadata.

## 25) Best-Practice Findings (External)
- React app decomposition: component-driven hierarchy and ownership boundaries.
  - https://react.dev/learn/thinking-in-react
- FastAPI larger app structure and dependencies.
  - https://fastapi.tiangolo.com/tutorial/bigger-applications/
  - https://fastapi.tiangolo.com/tutorial/dependencies/
- OWASP authorization controls and privilege checks.
  - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- WCAG contrast/focus for command UI.
  - https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
  - https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- OpenTelemetry trace concepts for observability model.
  - https://opentelemetry.io/docs/concepts/signals/traces/

## 26) Prioritized Roadmap
### Phase 1 (required first)
1. Fix extraction reliability before UI polish (compile-clean extraction first).
2. Reduce shell risk and establish stable page module boundaries.
3. Enforce overview/tasks-first entry behavior.
4. Stabilize attention-to-route workflows.
5. Keep backend behavior unchanged while improving structure.

### Phase 2
1. Formalize shared components/layout for consistent panels, notices, empty/loading/permissions states.
2. Improve role-aware navigation and default views.
3. Strengthen cost/high-risk highlighting and failure drilldown.
4. Clean trace, review, and evaluation routing.

### Phase 3
1. Backend modularization for agent/graph services and trace schema as needed.
2. Advanced governance surfaces and metrics.
3. Advanced frontend routing / router migration after component shell stabilizes.

## 27) Phase 1 Quick Wins
- Clean compile defects in extracted pages before broader migration.
- Wire extraction to shell without behavior change.
- Add predictable empty/loading/error/disabled patterns at shell-level.
- Keep Overview + My Tasks as first-run surface.

## 28) Phase 2 Structural Improvements
- Shared page/layout tokens,
- role-specific action cards,
- high-signal quick links,
- trace-driven review path.

## 29) Phase 3 Advanced Features
- OTel/span export,
- enterprise RBAC/ABAC,
- provider secrets and enterprise observability.

## 30) Risks if UI Polished Before Backend Process Readiness
- Cosmetic maturity without operational flow = interview-risk.
- Long-term maintenance risk if monolith grows while pages are only visually redesigned.
- Role confusion and permission ambiguity if action intent is not made explicit.

## 31) Severity-Ranked Gap List
### P0
- **Monolithic shell concentration risk**: `frontend/src/app/AppShell.tsx` is 8,623 lines and still contains many major page functions.
- **Not behavior-safe extraction state**: `frontend/src/pages/DatasetsPage.tsx` and `DocumentsPage.tsx` are untracked and contain TSX/logic issues that currently block build.
- **Build not clean for page refactor state**: `npm run build` currently fails with syntax errors.

### P1
- Workflow-first orientation not fully enforced for overview/tasks → page actions.
- Permission intent not yet globally standardized in every major page state.
- Trace/cost/evaluation actionability remains fragmented.

### P2
- Visual density and copy tone vary by section.
- Missing standardized component patterns for shared operations.

### P3
- Enterprise-grade RBAC/ABAC and trace export are future maturity items.

## 32) Current Evidence Snapshot
- `frontend/src/App.tsx`: 3 lines (thin export wrapper).
- `frontend/src/app/AppShell.tsx`: 8,623 lines.
- `frontend/src/pages`: Overview/Tasks/Members/Audit partially extracted; Datasets/Documents also exist but not integrated.
- `frontend/src/pages/OverviewPage.tsx` compiles check failure currently due malformed assignment.
- `frontend/src/pages/DocumentsPage.tsx` compiles check failure due JSX close-tag mismatch.
- Backend major route and service files are split by domain, but several (e.g., `agent_service.py`, `support_agent_graph.py`, `agents.py`) remain large.

## 33) First 5 Implementation Tickets

### Ticket 1 (required gate): UX-0A — Safe Shell-to-Page Wiring Without Behavior Change
**Goal**
- Use existing extraction work to complete reliable wiring of `Datasets` and `Documents` page modules and remove those panel renderers from `AppShell`.
- Fix all syntax/type errors created by extraction.

**Acceptance**
- `npm run build` must pass.
- All existing behaviors preserved.
- `AppShell` no longer owns monolithic rendering for those pages.

### Ticket 2: UX-0B — Shared Architecture Extraction (No Visual Redesign)
**Goal**
- Introduce shared route-like page composition for all major tabs (even if still rendered by activeTab switch): Overview, Tasks, Datasets, Documents, Agents, Tools, Guardrails, Trace, Reviews, Evaluations, Costs, Prompts, Models, System, Members, Audit, Settings.

**Acceptance**
- Smaller shell function surface,
- consistent props boundaries,
- same API calls still triggered.

### Ticket 3: UX-1 — Black-and-White Admin Console Scaffold
**Goal**
- Add shared layout primitives, status banners, quick links, and decision-first card patterns.
- Keep backend behavior unchanged.

### Ticket 4: UX-2 — Workflow Entry Dashboard
**Goal**
- Make Overview + My Tasks the standard entry point:
  - workspace role and permissions,
  - next action,
  - attention queue.

### Ticket 5: Audit-Backed Production Integrity Checks
**Goal**
- Add explicit user-facing acceptance checks:
  - attention routing leads to concrete pages,
  - role gating visibility,
  - trace-first inspection path,
  - cost/error high-signal card actions.

## 34) Risks and Tradeoffs
- **Tradeoff:** cleaning shell first delays visual redesign but avoids introducing UI behavior drift.
- **Risk:** partial extraction without end-to-end wiring can create regressions; therefore build-validated completion is required per ticket.
- **Tradeoff:** strict modularization initially increases prop plumbing and migration scope; this pays off in maintainability and interview review quality.
