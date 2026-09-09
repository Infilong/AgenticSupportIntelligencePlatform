# Frontend guidance

Scope: this directory and its descendants. Read the [root director](../AGENTS.md).
See [status](../docs/STATUS.md) for current implementation and verification progress.

## Ownership and design

- Follow the workbench direction in [architecture](../docs/ARCHITECTURE.md) and the
  frontend topology in [release plan](../REBUILD_PLAN.md).
- For quality/usage metrics, read [quality guidance](src/features/quality/AGENTS.md).
- Render server decisions; never implement authorization or business rules only in the UI.
- Separate rendering, state/hooks, API access and validation. Keep components cohesive.
- Give each screen a clear primary action. Reveal processing detail progressively; avoid
  repeated summaries, competing editors and raw implementation terms in user journeys.
- Preserve original messages, responses, citations and attempt history as distinct views.
- Support EN/JA/ZH, keyboard navigation, visible focus and understandable empty/error states.
- Read [backend guidance](../backend/AGENTS.md) when changing an API contract with its owner.

## Verification

- Use [runbook](../docs/RUNBOOK.md) for working commands and browser setup.
- Check affected real journeys against UX and relevant feature gates in
  [acceptance](../docs/ACCEPTANCE.md), including denied actions and recovery from errors.
- Inspect browser screenshots/traces for layout, small screens and zoom; type checks alone
  do not prove usable UI. Synthetic pages do not prove application behavior.
- Keep provider keys and protected data out of client bundles and browser logs.
- `src/api/schema.d.ts` is generated from backend OpenAPI; its size is an explicit generated
  contract exception. Regenerate it with the runbook command; never edit it manually.
