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
