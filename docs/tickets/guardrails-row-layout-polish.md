# Guardrails Row Layout Polish

## Goal
Make the Guardrails page read as a top-to-bottom workflow instead of a multi-column dashboard.

## Context
The shared app UI now favors full-width page sections with compact grids only for repeated metrics or card internals. Guardrails still had a two-column hero, multi-column filter area, two-column workbench, and multi-column guardrail card board.

## Implemented Behavior
- Guardrails hero is one row section with the posture card below the explanation on narrow/full layouts.
- Filter controls stack as row sections instead of competing columns.
- Guardrail policy cards render as full-width rows.
- Recent failures panel is a normal row section instead of sticky side content.
- Compact metric grids remain inside cards where they improve scanning.

## Verification
- Run `npm --prefix frontend run build`.
- Open Guardrails and confirm major sections stack top-to-bottom.
- Confirm card internals still fit on desktop and mobile widths.
