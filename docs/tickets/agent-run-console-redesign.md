# Agent Run Console Redesign

## Goal
Make the Support Agent page feel like a professional operations console instead of a set of disconnected controls. A user should immediately understand how to pick an agent, choose a realistic scenario, run the LangGraph workflow, and inspect the result.

## Implemented
- Replaced the old Agent page layout with a guided run console.
- Added a top-level Support Agent hero section with selected-agent controls.
- Added readiness cards for agent selection, indexed knowledge, pending reviews, and latest trace availability.
- Converted prompt chips into scenario cards with language, expected route, and scenario purpose.
- Added a stronger latest-outcome panel with direct next actions: inspect trace, resolve review, and cost ledger.
- Moved runtime tuning into a dedicated Developer Controls section.
- Added responsive CSS for desktop and smaller viewports.

## Product Rationale
The previous page exposed the backend pieces but did not create a clear workflow. This version makes the expected operator path visible while preserving admin/developer controls for token budget, confidence threshold, retrieval top K, and retrieval score.

## Verification
- `npm run test` -> passed
- `npm run build` -> passed
- Docker rebuild: `docker compose up -d --build frontend` -> passed
- Live endpoint check -> API health OK and frontend returned HTTP 200
