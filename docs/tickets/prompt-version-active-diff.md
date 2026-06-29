# Prompt Version Active Diff

## Goal
Make prompt operations safer by letting developers compare a prompt history version with the active prompt version for the same prompt family and language.

## Context
Prompt templates can already be created, activated, archived, listed, and traced through AI run ledger entries. The remaining prompt-ops gap was that users had to open full source blocks manually to understand how a candidate or older version differs from the active version.

## Requirements
- Use real prompt template history data from the existing workspace-scoped API.
- Compare only versions that share the same prompt name and language.
- Do not invent evaluation outcomes or fake prompt quality metrics.
- Keep the diff bounded so long prompt sources do not stretch the page.
- Keep active prompt versions visually clear and activation controls unchanged.

## Non-goals
- Do not implement prompt-version evaluation regression analysis in this ticket.
- Do not add backend schema changes.
- Do not add a full unified diff library or complex text editor.
- Do not compare unrelated prompt families or languages.

## Implementation
- Added deterministic line-level prompt comparison helpers in the frontend.
- Added a Compare with active panel for non-active prompt versions when an active same-family prompt is loaded.
- Shows added, removed, changed, and unchanged line counts plus the first changed lines.
- Added monochrome wrapping styles for prompt diff previews.

## Validation Plan
- Run frontend typecheck.
- Run frontend production build.
- Run frontend test wrapper.
- Run diff whitespace check.

## Validation
- cd frontend && npm run typecheck: passed.
- cd frontend && npm run build: passed.
- cd frontend && npm test -- --run: passed.

## Human Review Checklist
- Create or load at least two versions of the same prompt and language.
- Confirm inactive/history versions show Compare with active.
- Confirm active versions do not show a self-comparison.
- Confirm long prompt lines wrap and do not widen the card.
- Confirm activation/archive controls still work as before.

## Interview Notes
This ticket improves prompt governance without pretending to solve quality evaluation. It gives developers a concrete source-level review workflow before activating a prompt, while evaluation-by-prompt-version remains a larger future ticket that should use actual evaluation runs and cost/quality metrics.
