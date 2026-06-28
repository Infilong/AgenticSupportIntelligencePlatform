# Bounded Prompt And Model Admin Catalogs

## Goal
Keep prompt-template and model-config administration usable as workspace history grows. These are AI platform control-plane assets, so their history views should behave like searchable operations boards rather than unbounded card dumps.

## Context
Prompt templates and model configs already have backend lifecycle controls: list, create, activate, archive, and owner-only write access. The frontend history panels still rendered every loaded item and expanded full prompt source inline, which becomes noisy after many versions.

## Requirements
- Add search and status filters to prompt version history.
- Add search and status filters to model config history.
- Bound rendered prompt/model cards and show a clear note when more matches exist.
- Keep prompt source inspectable but collapsed by default.
- Preserve existing create, activate, archive, and show-archived behavior.
- Do not add folders yet; these remain small admin catalogs, not file-backed libraries.

## Non-goals
- Do not change backend schema or APIs.
- Do not add server-side pagination in this ticket.
- Do not change model routing or prompt activation semantics.

## Test Plan
- Run frontend production build.
- Run `git diff --check`.

## Human Review Checklist
- Confirm prompt/model pages are easier to scan with many versions.
- Confirm long prompt text no longer dominates the page by default.
- Confirm activation/archive controls remain clear and permission-aware.

## Interview Notes
This is a control-plane UX improvement: production AI systems need prompt and model history, but history must remain searchable, bounded, and auditable so operators can find the active route or regression-causing change quickly.
