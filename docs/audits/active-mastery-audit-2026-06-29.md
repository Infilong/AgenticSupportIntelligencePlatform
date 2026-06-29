# Active Platform Audit (Pre-Implementation Gate)

Date: 2026-06-29
Scope: `/home/infilong/project/AgenticSupportIntelligencePlatform`
Status: **Audit complete. No implementation changes beyond governance/docs yet in this gate.**

## 1) Current product assessment

### Backend strengths
- Real multilingual AI platform foundation is present: auth/workspace/membership, dataset curation, multilingual knowledge ingestion, LangChain abstractions, LangGraph orchestration, graph traces, tool calls, guardrails, human-review routing, evaluation runs, AI run ledger, token/cost accounting, audit logs.
- Permissions and role-aware endpoints exist in FastAPI dependency layer and domain routes.
- Existing operational scaffolding for folders, archive states, attention counters, run history, and evaluation summaries is in place.

### Frontend strengths
- UI is already split into `pages` and `AppShell` composition, and has functional flows for overview/tasks/members/datasets/knowledge/agents/runs/reviews/evals/costs/admin.
- Backend wiring and API contracts are mostly reachable from UI paths.

### Main implementation risk
- Core execution and trace logic exists, but frontend architecture and page composition are still concentrated in oversized modules, which undermines “professional platform” credibility.

## 2) What feels toy-like now

- Feature islands are present, but not organized as explicit first-class workflows.
- High-signal actions (review, trace, cost anomalies, failed runs) are present but not consistently prioritized as guided operations.
- In some places, user flow looks “feature inventory” rather than “operational runbook”.

## 3) What is confusing now

- New users do not get one obvious operational order from workspace selection → permission context → active tasks → action → resolution.
- Some high-impact actions are mixed with utility controls.
- “What changed / why / next step” is uneven across pages.
- Sidebar groups are more feature-oriented than workflow-oriented.

## 4) What does not match a professional black-and-white admin style

- Current styling is serviceable but does not yet enforce a consistent layout system with clear action hierarchy.
- Visual rhythm varies per page and per section because ownership patterns differ across extracted and inline sections.
- The architecture signals prototype-style coupling more than a console-grade structure.

## 5) Navigation/sidebar problems

- Sidebar is collapsible and role-filtered in parts, but not yet architecturally stable as a route-first workflow map.
- Current selection/panel mapping is clear, but transition language and quick-link conventions are inconsistent.
- Some critical destinations are hidden inside large mixed panels, not surfaced as dedicated “next action” destinations.

## 6) Missing permission-aware UX

- Backend enforcement is strong and explicit.
- Frontend permission narration (who can do what now) is incomplete: controls are often present but role path framing is still weak.
- Restricted actions should be shown with explicit reason and actionable alternatives, not just hidden or implicit.

## 7) Missing task/attention workflow

- Attention data exists and APIs expose task-like states.
- The attention model is not yet the default top-level operating loop for all roles; users still need to infer sequence.
- Priority-to-action links are present in practice but not consistently first-class in layout.

## 8) Missing backend support for professional UI

- No blocking schema/API gaps for audit-tied UX recovery.
- Backend endpoints are mostly present, but frontend currently does extra client-side orchestration for summaries and cross-surface navigation metadata.
- Improvement opportunity: concise summary payloads for dashboard attention cards and deterministic jump metadata for run/review/cost flow.

## 9) Data and tool organization problems

- Foldering exists for large collections.
- Tooling/tool-policy surfaces and guardrail/product governance remain distributed across monolithic shell rendering paths.
- As dataset/knowledge/tool volume grows, current cross-surface list ownership will become harder to scan and test.

## 10) UI/UX gaps

- No explicit route-level navigation yet (tab/panel orchestration is in use).
- Shared primitives and interaction contracts are inconsistent between older and newer page modules.
- Empty/loading/error/permission-empty states are still inconsistent across surfaces.

## 11) Backend / data-model gaps

- No urgent migration blockers for the next UX-0 ticket.
- Optional but useful additions for UX quality:
  - richer operational metadata on mutable resources (archived/deactivated context + actor audit fields where needed),
  - indices supporting bounded list sorting/filtering by `workspace_id/status/folder_id/created_at`,
  - stable cross-entity reference fields for trace → run → review links where currently inferred.

## 12) Agent workflow gaps

- Runtime workflow is robust: LangGraph nodes, checkpoints, retriever/guardrail/tool branches, confidence routing, and human-review hooks are implemented.
- UI gap is the operational narrative (input → steps → checks → routing → final answer/cost → trace/review).

## 13) Traceability gaps

- Trace tables/events are present and recorded.
- Missing piece is navigation UX coherence: easier movement from attention/dashboard to exact node/guardrail/model-call detail with stable drill-down path.

## 14) Guardrail/governance gaps

- Guardrail coverage is implemented.
- Governance UX still reads less like operator controls and more like diagnostics, especially for policy lifecycle, severity, and remediation suggestions.

## 15) Evaluation gaps

- Evaluation run and metrics framework exists.
- Product-grade UX needs better case-level regression framing, failed-case drill-down, and baseline comparison surfaced as operator action cards.

## 16) Cost/token observability gaps

- Token/cost accounting and summaries exist.
- Missing clarity layer: outlier highlights and contextual actions (what to do with high-cost/failing routes).

## 17) Admin/developer experience gaps

- Admin surfaces and developer surfaces are present but not yet arranged by workflow and role-first priorities.
- Reviewer workflow is present but could be clearly separated with reduced cognitive noise.

## 18) Best-practice findings (applicable)

- React guidance strongly favors decomposition by responsibility and data flow boundaries.
  - https://react.dev/learn/thinking-in-react
  - https://react.dev/learn/passing-props-to-a-component
- FastAPI recommends dependency-based authorization and modular domain routers.
  - https://fastapi.tiangolo.com/tutorial/dependencies/
  - https://fastapi.tiangolo.com/tutorial/bigger-applications/
- OWASP authorization principles support explicit, enforced permission checks.
  - https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- WCAG contrast/focus guidance aligns with high-clarity admin dashboards.
  - https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
  - https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- OpenTelemetry trace semantics are useful for conceptual flow design.
  - https://opentelemetry.io/docs/concepts/signals/traces/

## 19) Recommended information architecture

```text
Overview / Operations First
├─ Overview dashboard
├─ My tasks / attention

Build
├─ Data
├─ Knowledge
├─ Agents
├─ Tools
└─ Guardrails

Operate
├─ Runs
├─ Trace
├─ Human review
└─ Costs

Evaluate
├─ Evaluation suites
├─ Evaluation runs
└─ Regression / baseline

Admin
├─ Workspace / members
├─ Roles / permissions
├─ Prompts / models
├─ Settings
└─ Audit logs
```

## 20) Recommended sidebar/navigation plan

- Keep sidebar collapsible with two stable visual states.
- Show quick links at top: Overview, My Tasks, Active Reviews, Latest Trace, High-cost runs.
- Keep current workspace/role visible and stable.
- Permission-aware visibility and disabled-with-reason patterns.
- Ensure one-click jump paths from cards to the right page surfaces.

## 21) Recommended dashboard plan

- Header row: workspace, selected role, permission posture.
- Middle row: attention cards (pending reviews, failed runs, high-cost, guardrail blocks, indexing issues).
- Lower row: recent traces/evals with direct links.
- Every card includes: what happened, why it matters, next action, destination page.

## 22) Role/permission-aware UX plan

- **Owner/Admin:** workspace settings, members, budget/provider policy, audit, cost controls.
- **Developer:** agents/tools/models/prompts, trace/cost guardrail diagnostics, eval posture.
- **Reviewer:** review queue, evidence cards, citations, decisions.
- **Viewer:** read-only observability with clear limitation messaging.

## 23) Agent / Tool / Guardrail / Evaluation / Cost page plan

- **Agents:** agent catalog + health + run/step linkage + model/provider usage.
- **Tools:** catalog, input/output schema, permissions, usage/error history.
- **Guardrails:** policy list + severity + pass/fail + routing outcome + trace linkage.
- **Evaluations:** language-aware suites, baseline mode view, failed-case drill-down.
- **Costs:** workspace/agent/model/run views, budget risk flags, cost trend cards.

## 24) Backend/API gap list

- No hard blockers for UX-0.
- Optional high-value shaping tasks:
  - compact role/workspace attention summary endpoints,
  - deterministic action-link metadata in list APIs,
  - stable trace-card summary endpoint for dashboard and navigation.

## 25) Database/model gap list

- No mandatory schema changes required for first UX-0 refactor.
- Likely additions in later phases: richer actor/lifecycle metadata for mutable admin objects and stronger trace-to-review foreign-link integrity where currently inferred.

## 26) Prioritized implementation roadmap

### Phase 1 (stability + architectural cleanup)
1. Complete frontend extraction so no heavy operational surface logic remains in `AppShell`.
2. Stabilize shared page primitives and workflow cards.
3. Standardize role-aware context and permissions messaging.
4. Add deterministic cross-page links and consistent attention flow.

### Phase 2 (professional structure)
1. Route-like page architecture (`AppShell` + page modules + components/hook boundaries).
2. Folder-first list handling and bounded pagination/search.
3. Introduce shared loading/error/empty/permission states.
4. Dashboard action model with role-specific defaults.

### Phase 3 (advanced platform quality)
1. Route migration to real route layer if needed.
2. Expand governance + evaluation + policy lifecycle surfaces.
3. Add stronger cost anomaly/risk workflows and observability signals.

## 27) Phase 1 quick wins

1. Finish extraction of remaining in-shell page blocks.
2. Add consistent header + quick-link patterns across Overview/Tasks/agents/cost/eval/review areas.
3. Unify role/permission disabled-state messaging.
4. Add smoke-check path: overview → task/review → trace → run details.

## 28) Phase 2 structural improvements

1. Introduce shared component modules and avoid monolithic functions.
2. Add API client/service boundaries on frontend (fetch + state separated).
3. Improve folder/list controls for large collections.
4. Expand traceability navigation with stable IDs and deep links.

## 29) Phase 3 advanced features

1. Backend API summary endpoints for role-aware dashboard cards.
2. Full cost/actionability workflows and remediation actions.
3. Optional router migration and deeper admin operations.

## 30) Risks if UI improved without backend alignment

- High visual polish would not fix incorrect decision flow if backend semantics are not surfaced cleanly.
- Monolithic UI ownership can still hide missing permission failures and regressions.
- Workflow confidence drops if users cannot move from summary card directly to evidence and decision surface.

## Severity-ranked gap list

### P0 (critical for professional credibility)
1. `frontend/src/app/AppShell.tsx` remains oversized and high-coupling (8,182 lines).
2. Large in-shell feature rendering still concentrates orchestration, fetching, state, and composition.
3. Lack of stable workflow-first entry model for all user roles.

### P1 (important)
1. Permission-aware UX messaging is inconsistent across pages.
2. Attention/first-action flow not consistently dominant from Overview.
3. Traceability navigation between task, trace, review, and cost surfaces can still require extra user reasoning.

### P2 (polish)
1. Visual hierarchy and spacing still vary across modules.
2. Shared component reuse incomplete.
3. No route-level navigation yet.

### P3 (future)
1. Enterprise RBAC/SSO and advanced cloud observability scope.
2. OpenTelemetry exporter/dashboard stack beyond current scope.

## First 5 implementation tickets (post-audit)

### Ticket 1 — UX-0A: App shell extraction hardening (no behavior change)
- Scope: move major in-shell inline sections into dedicated page-level modules already present in `frontend/src/pages` while preserving behavior.
- Focus: reduce operational coupling in `frontend/src/app/AppShell.tsx` under 300 lines target; no API logic/behavior changes.
- Files: `frontend/src/app/AppShell.tsx` and page modules.

### Ticket 2 — UX-0B: Shared workflow presentation shell
- Scope: standardize page scaffold (`PageHeader`, quick actions, status banner, empty/loading/error, permission reason states).
- Focus: consistent visual hierarchy and role-aware affordances.

### Ticket 3 — UX-1: Attention-first dashboard
- Scope: make Overview role-aware and task-driven.
- Focus: workspace/role context first, then attention list, then direct action links.

### Ticket 4 — UX-0C: Collapsible navigation restructure
- Scope: stabilize sidebar with explicit grouped workflow map and quick-jump links.
- Focus: predictable route-like identity and collapsed-state behavior.

### Ticket 5 — UX-2: Review/Trace/Cost flow integration
- Scope: from each attention card, deterministic jump to review or run trace, then to cost/action context.
- Focus: traceability-first issue resolution loop.
