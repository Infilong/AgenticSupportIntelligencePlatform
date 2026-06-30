# GitHub-Style Single-Column UI Polish

## Goal
Make the application easier to understand at a glance by removing confusing multi-column workbench layouts and applying a GitHub-like visual system: white and black as the base, with semantic color for links, active state, success, warning, and danger.

## User Feedback Addressed
- Main content must read top-to-bottom, not as multiple columns with large empty spaces.
- Collapsed left navigation must not show clipped text or characters outside boxes.
- Collapsed navigation should use symbols that indicate function, not two-character abbreviations.
- Visual hierarchy should feel closer to GitHub: restrained, mostly white/black/gray, with color used for meaningful state.

## Implementation
- Added `frontend/src/github-theme.css` for GitHub-like colors, buttons, sidebar, nav tokens, and semantic status colors.
- Added `frontend/src/workflow-rows.css` for single-column workflow layout overrides across overview, tasks, data, knowledge, agents, reviews, traces, evaluations, costs, admin, and settings surfaces.
- Imported both override stylesheets after the existing global stylesheet in `frontend/src/main.tsx`.
- Replaced two-character sidebar nav tokens in `frontend/src/app/AppShell.tsx` with single symbols.

## Responsibility Split
- Theme and semantic color: `frontend/src/github-theme.css`.
- Single-column row layout and sticky workflow shortcuts: `frontend/src/workflow-rows.css`.
- App bootstrap stylesheet order: `frontend/src/main.tsx`.
- Navigation symbol data: `frontend/src/app/AppShell.tsx`.

## Validation
- `npm --prefix frontend run build` passed.
- `docker compose -p agenticsupportintelligenceplatform up -d --build frontend` completed.
- `curl http://127.0.0.1:5173` returned HTTP 200.
- `curl http://127.0.0.1:8000/health` returned `{"status":"ok","service":"api"}`.

## Known Verification Blocker
- `npm run test:e2e -- --project=chromium` could not launch Chromium because WSL is missing `libnspr4.so`.
- This is an environment dependency issue, not an app compile failure.

## Manual Review Checklist
- Open `http://127.0.0.1:5173`.
- Collapse the sidebar and confirm every nav item stays inside its box.
- Check pages with previous multi-column layout: Dashboard, Tasks, Knowledge, Agents, Human review, Runs & traces, Evaluations, Usage & costs, Prompts, Models, System health.
- Confirm sections read top-to-bottom and important states use semantic color.
