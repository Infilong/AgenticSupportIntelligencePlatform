# Frontend Architecture Decomposition

## Goal
Reduce the frontend coupling risk by splitting the oversized app shell into focused modules while preserving current behavior, visual direction, and API behavior.

## Context
The current UI has improved information architecture and GitHub-like styling, but the implementation is still difficult to maintain. frontend/src/app/AppShell.tsx is over 8,000 lines and contains layout, navigation, API calls, state transitions, page rendering, resource operations, and trace/evaluation details. This conflicts with codingRules.md and makes future UI fixes risky.

Relevant docs:
- codingRules.md
- docs/PROJECT_CONTEXT.md
- docs/ui-design-system.md
- docs/tickets/information-architecture-navigation-cleanup.md
- docs/tickets/github-single-column-ui-polish.md

## Requirements
- Preserve current user-visible behavior first.
- Keep the canonical IA: Account -> Dashboard/My Tasks -> Build -> Operate -> Evaluate -> Admin -> Settings.
- Keep the sidebar as navigation plus current workspace context only.
- Extract API/network helpers away from page rendering code.
- Extract shared UI primitives and list/pagination behavior where reuse is already real.
- Split page containers from large page-specific sections when practical.
- Keep each new file focused and preferably under 300 lines.
- Maintain existing permission checks and backend-enforced workspace isolation assumptions.
- Preserve or improve browser smoke coverage for focus stability, sidebar collapse, bounded lists, and core demo navigation.

## Non-goals
- No backend API changes.
- No database migrations.
- No new product features.
- No visual redesign beyond incidental markup preservation needed for decomposition.
- No new dependency unless explicitly approved.
- No route-system rewrite unless a smaller split proves impossible.

## Design Plan
1. Map responsibilities currently inside AppShell.tsx: auth/session, workspace selection, navigation, API helper, shared actions, tab rendering, page data orchestration, and page presentation.
2. Extract low-risk shared modules first:
   - API client and request helpers;
   - navigation/tab definitions;
   - common pagination/list helpers;
   - shared empty/status/metric primitives if they are still inside the shell.
3. Split layout/navigation from active page rendering:
   - app shell layout;
   - sidebar/topbar;
   - workspace context summary;
   - active tab dispatcher.
4. Move page-specific state/rendering into page container modules incrementally. Start with the least coupled pages, then Data/Knowledge/Agents/Traces/Reviews/Evaluations.
5. Keep each extraction behavior-preserving. Run typecheck/build and targeted browser smoke after each meaningful slice.
6. Stop after one reviewable slice if the diff grows too large.

## Files Likely To Change
Expected directories, not a fixed final list:
- frontend/src/app/AppShell.tsx
- frontend/src/app/navigation.ts
- frontend/src/app/apiClient.ts
- frontend/src/app/hooks/
- frontend/src/app/shared/
- frontend/src/pages/
- frontend/tests/e2e/review-ux-smoke.spec.ts
- docs/tickets/frontend-architecture-decomposition.md

## Database Migrations
None.

## API Changes
None. Existing backend routes and response shapes must remain unchanged.

## Test Plan
- npm --prefix frontend run typecheck
- npm --prefix frontend run build
- Existing Playwright smoke test if browser dependencies are available.
- Manual browser check if Playwright cannot run in WSL:
  - login/account/workspace selection;
  - sidebar expand/collapse;
  - Data and Knowledge lists/folders;
  - Agent run to trace;
  - Human review queue;
  - Evaluation and Usage & costs pages.

## Acceptance Criteria
- AppShell.tsx is materially smaller and no longer owns every frontend responsibility.
- Extracted files have clear names and focused responsibilities.
- User-visible behavior is preserved.
- Typecheck and build pass.
- Browser smoke or documented manual QA covers the high-risk flows.
- No backend behavior or API contract changes.
- No new broad UI redesign is mixed into the decomposition diff.

## Risks
- Behavior regressions from moving state between components.
- Import cycles between shared modules and page containers.
- Over-extraction into generic utilities that are harder to follow than the original code.
- Diff becomes too large for review. Stop and split if the first slice exceeds the project review budget.

## Human Review Checklist
- Can you find navigation definitions without opening the whole app shell?
- Can you find API request behavior separately from rendering?
- Did the ticket preserve the current UI and workflow?
- Are new files cohesive and small enough to review?
- Did typecheck/build and browser smoke/manual checks run?
- Are there any hidden permission or workspace-scope assumptions moved into frontend-only logic?

## Operating Notes
This is a prerequisite for reliable future UI work. After the frontend is less coupled, create a separate backend decomposition ticket for support_agent_graph.py, agent_service.py, agents.py, and evaluation_runner.py.
