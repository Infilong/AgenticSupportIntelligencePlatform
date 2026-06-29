# Platform UX And Backend Recovery Audit

Date: 2026-06-29
Scope: frontend architecture, backend structure, product information architecture, permissions, AI platform logic, and roadmap before further implementation.
Status: audit only. No application code changes are approved by this document.

## Executive Assessment

The product already has serious backend concepts: workspaces, role permissions, resource folders, LangGraph runs, graph steps, tool calls, AI run ledger, guardrails, human review, evaluations, cost summaries, audit logs, and system health. That is strong portfolio substance.

The credibility problem is presentation and code structure. The frontend concentrates too much UI, state, API orchestration, page rendering, and data mapping in one file. The backend is better organized by domain, but several core agent/evaluation files are too large for easy review. The app therefore has strong platform ingredients but currently feels confusing and toy-like because users cannot understand the workflow quickly and maintainers cannot reason about the code in small modules.

## Evidence From Current Worktree

- `frontend/src/App.tsx`: 9,149 lines, 126 `useState` calls, 77 async functions, and 19 page/panel functions.
- `frontend/src/styles.css`: 3,797 lines with mostly grayscale tokens and many grid/workbench-specific rules.
- Frontend has only `App.tsx`, `main.tsx`, and `styles.css` under `frontend/src`; no component/page/hook/API/type module structure yet.
- Largest backend files: `support_agent_graph.py` 910 lines, `agent_service.py` 787 lines, `api/v1/agents.py` 660 lines, `evaluation_runner.py` 572 lines.
- Largest backend tests: `test_agents.py` 1,325 lines, `test_resource_folders.py` 771 lines, `test_evaluations.py` 765 lines.
- Backend evidence shows real workspace scoping and platform models exist: `AIRun`, `GraphRun`, `GraphStep`, `ToolCall`, `RetrievalTrace`, `GuardrailResult`, `HumanReview`, `EvaluationRun`, budget policies, attention tasks, and role permissions.

## Best-Practice Findings Applied

These findings are used as design constraints, not as designs to copy:

- React official guidance emphasizes breaking UI into a component hierarchy and identifying minimal state ownership. This supports extracting pages, components, hooks, and API clients from `App.tsx`. Source: https://react.dev/learn/thinking-in-react
- FastAPI official guidance for larger applications uses `APIRouter` across multiple files. This supports splitting oversized route files such as `api/v1/agents.py` by resource surface. Source: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- OWASP authorization guidance centers server-side access control, least privilege, and deny-by-default behavior. This supports keeping permission enforcement in backend dependencies/services, not only UI hiding. Source: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- WCAG guidance requires contrast and visible focus states. This supports high-contrast monochrome UI with semantic status accents and consistent keyboard-visible controls. Source: https://www.w3.org/TR/WCAG22/
- OpenTelemetry trace concepts model execution as traces made of spans. This supports presenting LangGraph node executions, model calls, tool calls, guardrails, and routing decisions as a trace timeline. Source: https://opentelemetry.io/docs/concepts/signals/traces/
- Mature design systems treat side navigation as a stable orientation mechanism with clear current location and grouped destinations. This supports grouped, permission-aware navigation with collapsed and expanded states. Source anchors: https://m3.material.io/components/navigation-drawer/guidelines and https://developer.apple.com/design/human-interface-guidelines/sidebars

## Severity-Ranked Gap List

### P0: Critical For Professional Credibility

1. Frontend god file: `App.tsx` mixes auth, workspace state, API calls, page rendering, mutations, validation, navigation, and inspectors.
2. No route/page/component architecture: major product areas are inner functions rather than independent page modules.
3. Current UI does not clearly teach the workflow: users see many panels but no obvious step sequence or next action.
4. Trace viewer is not visually positioned as the core proof of agent execution; it should be the strongest product page.
5. Backend graph orchestration is too concentrated in `support_agent_graph.py`, making LangGraph nodes, routing, persistence, and budget logic hard to debug.
6. Agent API/service files are too large for staff-level review and should be split by configs, runs, traces, and workflow.
7. Browser-level QA is not reliable in WSL because Playwright Chromium currently fails on missing system dependency `libnspr4.so`; the Windows Chrome CDP fallback works but is not an integrated project command.

### P1: Important

1. Sidebar groups exist but still feel like a feature list instead of a role-aware workflow map.
2. Dashboard cards need to answer what happened, why it matters, and what to do next.
3. Reviewer, developer, admin, and viewer experiences are not separated enough by role intent.
4. Data/knowledge pages have resource management but need a vertical step-by-step flow: import/upload, organize, inspect, validate readiness.
5. Tools and guardrails are first-class enough in backend, but pages need clearer operational meaning and trace linkage.
6. Evaluation and cost pages expose data but should better connect regressions/high-cost runs to traces and next actions.
7. Tests are large by domain and should be split by behavior so failures are easier to localize.

### P2: Polish

1. Monochrome style needs semantic status accents: blue/info, green/success, amber/warning, red/danger, indigo/AI. The base can remain black-and-white.
2. Empty/loading/error states should be standardized.
3. Forms need clearer primary/secondary action hierarchy and advanced-setting disclosure.
4. Raw JSON should be secondary/debug detail, not the main explanation.

### P3: Future Enhancement

1. Add real URL routing with React Router after page extraction is stable.
2. Add OpenTelemetry-compatible trace/span IDs if future integration is desired.
3. Add deeper provider secret management UI after local/demo provider readiness is clear.

## Required Audit Items

1. Current product assessment: Strong backend platform substance, weak frontend organization and workflow clarity.
2. What feels toy-like: too many generic panels, unclear next actions, weak role narrative, final-answer/demo feel stronger than operational trace story.
3. Confusing layout: side-by-side workbenches compete; users must scan horizontally and vertically without a stable page sequence.
4. Black-and-white mismatch: status and risk are not differentiated enough; monochrome is used as absence of hierarchy rather than a disciplined system.
5. Sidebar problems: grouped but still dense; collapsed state exists, but page purpose and current workflow stage are not obvious enough.
6. Permission-aware UX gaps: permissions are shown, but role-specific journeys are not primary; restricted controls need consistent explanation.
7. Task/attention gaps: attention queue exists but dashboard and pages should route users to concrete remediation actions.
8. Backend support gaps: most support exists, but missing/weak areas include richer agent descriptions/ownership, trace/span model clarity, integrated browser QA, and modular graph APIs.
9. Data/tool organization problems: resource folders exist, but Data/Knowledge/Tools should use the same workflow pattern and readiness language.
10. UI/UX gaps: no reusable page scaffold, quick links, workflow steps, status banners, problem lists, or consistent section panels.
11. Backend/data model gaps: possible need for agent description/owner metadata, richer run failure categories, trace/span correlation normalization, and persistent UI-facing dashboard summaries.
12. Agent workflow gaps: graph nodes exist, but node modules are not separated and the UI does not make the graph lifecycle dominant.
13. Traceability gaps: graph steps/tool calls/AI runs exist, but trace page should show a span-like timeline with inputs, outputs, costs, status, and routing decisions together.
14. Guardrail/governance gaps: guardrail results exist, but pages should clarify check, severity, action taken, policy, and related trace step.
15. Evaluation gaps: evaluation exists, but result pages need clearer baseline comparison, regression explanation, language grouping, and trace links.
16. Cost/token gaps: ledger exists, but dashboards should focus on high-cost runs, model/purpose breakdowns, budget risk, and remediation.
17. Admin/developer gaps: settings are broad; admin, developer, reviewer, and viewer modes need clearer boundaries.
18. Recommended IA: Overview, My Tasks, Agents, Runs/Traces, Data, Knowledge, Tools, Guardrails, Evaluations, Usage/Costs, Admin, Settings.
19. Recommended sidebar: grouped by Platform, Build, Operate, Evaluate, Govern, Admin/Settings; permission-filtered; collapsed labels/tokens remain usable.
20. Recommended dashboard: workspace status, role/permission summary, workflow checklist, attention cards, recent risky runs, eval regressions, cost/system health.
21. Role UX plan: reviewer-first review queue, developer-first traces/tools/evals, admin-first members/models/budgets/audit, viewer-first read-only status.
22. Backend/API changes required: split agent route/service/graph modules; add any missing summary endpoints after UI needs are proven.
23. Database/model changes required: no immediate migration is required for UX-0; likely future migrations for agent description/owner metadata and normalized trace/span identifiers.
24. Best-practice findings: listed above.
25. Prioritized roadmap: below.
26. Phase 1 quick wins: architecture split, page scaffold, sidebar/dashboard recovery, browser QA command.
27. Phase 2 structural improvements: backend agent graph/API split, workflow page redesigns, role journeys.
28. Phase 3 advanced features: real router, richer trace spans, provider secret UI, OpenTelemetry export path.
29. Risk if only UI improves: the app will look more professional but remain hard to maintain, and future features will keep accumulating in huge files.

## Revised Information Architecture

```text
Platform
- Overview
- My Tasks

Build
- Agents
- Data
- Knowledge
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
- System Health
- Audit
- Settings
```

The UI, API routes, service modules, and docs should use the same language where practical.

## Revised Dashboard Plan

The dashboard should become a workflow command center:

1. Workspace context: selected workspace, role, permission summary, health.
2. Recommended next action: one primary action based on readiness and role.
3. Workflow checklist: data, knowledge, agent, run, trace, review, evaluation, cost.
4. Attention queue preview: reviews, failures, guardrail blocks, eval regressions, high-cost runs.
5. Recent activity: latest runs, evaluations, audit events.
6. Admin/developer panels: shown only when permission allows.

## Role And Permission UX Plan

- Admin/platform owner: default emphasis on system health, members, models, budgets, audit, failed runs, governance.
- Developer/AI engineer: default emphasis on agents, graph traces, tools, guardrails, evaluations, model calls, failures.
- Reviewer: default emphasis on pending reviews, evidence, proposed answer/no-draft reason, approve/edit/reject controls.
- Viewer: default emphasis on read-only dashboard, traces, evaluations, costs if permitted, with disabled actions explained.

Backend remains source of truth. Frontend filtering improves clarity but must never be considered enforcement.

## Page Plans

### Agents

Structure: overview, active agent picker, runtime controls, model/budget/routing, workflow graph, recent runs, evaluation posture, run console. Split basic and advanced settings.

### Tools

Structure: tool catalog, schema/permission summary, enabled status, timeout/retry policy, usage history, error history, related traces.

### Guardrails

Structure: policy catalog, severity/action, where it runs, recent failures, related graph step/trace links, admin configuration.

### Runs / Traces

Structure: run summary, graph timeline, node detail, model calls, tool calls, guardrails, retrieval/citations, cost/latency, errors/retries, final route.

### Evaluations

Structure: run evaluation, baseline comparison, per-language metrics, regression list, case detail, trace links, cost/latency.

### Usage / Costs

Structure: spend summary, budget risk, high-cost runs, model/purpose/agent breakdowns, failed model/tool calls, ledger.

## Backend/API Gap List

- Split `api/v1/agents.py` into route modules for configs, runs, traces, and workflow responses.
- Split `agent_service.py` into config service, run service, trace service, and workflow summary helpers.
- Split `support_agent_graph.py` into graph builder, nodes, persistence, routing, budget helpers, and mock/provider helpers.
- Split `evaluation_runner.py` into run lifecycle, mode execution, scoring, metrics, and comparison helpers.
- Review all list endpoints for pagination/filters/totals consistency; much exists, but should be documented and enforced per page.
- Add summary endpoints only where frontend cannot efficiently compose data from existing APIs.

## Database/Model Gap List

No migration is needed before UX-0A. Candidate future migrations:

- `AgentConfig.description`, `owner_user_id`, and richer status metadata.
- Normalized trace/span correlation fields if trace UI needs stable span grouping beyond current `GraphStep` and `ToolCall` links.
- Provider secret/config metadata if real provider setup moves beyond local `.env` readiness.
- More explicit evaluation dataset/case ownership if evaluation curation becomes a product surface.

## Phased Roadmap

### Phase 1: Stop The Bleeding

1. UX-0A: split `App.tsx` into page modules without behavior change.
2. UX-0B: extract common components, navigation config, permission helpers, and API client modules.
3. UX-1: add shared design tokens/page scaffold for professional monochrome with semantic accents.
4. UX-2: rebuild dashboard as workflow command center.
5. QA-1: make browser smoke runnable from a project command in the current WSL/Windows setup.

### Phase 2: Product Workflow Recovery

1. Rebuild Data and Knowledge pages as vertical workflows.
2. Rebuild Agent, Trace, and Human Review pages around the stateful workflow.
3. Rebuild Evaluation and Cost pages around regressions, traces, and token economy.
4. Rebuild Tools/Guardrails/Admin pages with role-specific intent.
5. Split backend agent graph/service/API modules.

### Phase 3: Advanced Platform Depth

1. Add React Router after page modules are stable.
2. Add richer trace/span model and possibly OpenTelemetry export mapping.
3. Add provider credential/admin readiness flows.
4. Add richer role-specific dashboards and saved views.

## First 5 Implementation Tickets

### Ticket 1: UX-0A Page Module Extraction

Goal: split `App.tsx` page render functions into `frontend/src/pages/*` without changing behavior.
Files likely changed: `App.tsx`, new page files, possibly `frontend/src/app/navigation.ts`.
Backend impact: none.
Tests: `npm run test`, `npm run build`, browser smoke if available.
Risk: moving inner functions may require a large prop surface; keep it mechanical and stop if too broad.
Review checklist: no behavior change, no visual redesign, `App.tsx` line count meaningfully reduced.

### Ticket 2: UX-0B Shared Components And API Boundary

Goal: extract common `Badge`, `Metric`, `EmptyState`, `FolderPicker`, `ResourceFolderPanel`, and `api/client.ts`.
Backend impact: none.
Tests: frontend typecheck/build and smoke.
Risk: accidental semantic changes in shared components.

### Ticket 3: UX-1 Professional Design Scaffold

Goal: add tokens, page header, quick links, workflow step, status banner, problem list, and section panel components.
Backend impact: none.
Tests: frontend typecheck/build, browser screenshot review.
Risk: visual churn without workflow clarity; require screenshots.

### Ticket 4: UX-2 Workflow Dashboard

Goal: rebuild dashboard around workspace, role, permissions, next action, attention queue, workflow checklist, system/cost summary.
Backend impact: use existing membership, attention, cost, system health APIs; identify missing summary fields but do not fake them.
Tests: frontend plus API permission smoke for dashboard data.
Risk: overloading dashboard; keep role-based visibility.

### Ticket 5: BE-0A Agent Backend Modularization Plan And First Split

Goal: split agent graph or agent API/service into coherent modules without behavior change.
Backend impact: internal module boundaries only.
Tests: `uv run pytest -s -q tests/test_agents.py tests/test_langchain_support.py tests/test_tools.py`, then full backend if practical.
Risk: circular imports and trace regression.

## Risks And Tradeoffs

- A pure UI redesign will hide but not fix maintainability problems.
- A large refactor can break behavior invisibly; use mechanical extraction and strong tests first.
- React Router is desirable but should wait until page modules exist.
- Backend modularization is necessary but should follow the user-visible UX recovery because current confusion blocks review.
- Semantic accents are needed even in a black-and-white style; without them warnings and security signals are too easy to miss.
- Browser QA must be treated as a gate for UX claims; typecheck/build are insufficient evidence that the app feels professional.

## Approval Gate

No implementation should begin until this audit and roadmap are approved. After approval, implement Ticket 1 only.
