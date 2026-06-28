# Collapsible Sidebar and Black-and-White Shell

## Goal
Make the app shell feel like a professional AI platform console instead of a fixed, color-accented demo layout.

## Context
This implements the next roadmap item from `docs/professional-platform-audit.md`: collapsible sidebar and black-and-white visual system. It follows the active goal requirement that users should understand current workspace, role, permissions, navigation, and next actions without visual noise.

## Requirements
- Add a clear sidebar hide/show control.
- Preserve navigation usability in collapsed state with compact tokens and accessible labels.
- Keep the current page visually obvious in expanded and collapsed states.
- Adjust the main layout when the sidebar is collapsed so content is not hidden.
- Show workspace role and permission summary in the shell using current backend-supported ownership data.
- Move the frontend visual system toward high-contrast black, white, and neutral grays.
- Avoid adding fake backend role capabilities.

## Non-goals
- No new backend permission model.
- No member-management UI.
- No new URL routing or page split.
- No first-class Tools or Guardrails pages in this ticket.

## Implementation Record
- Added persisted `asi_sidebar_collapsed` state in `frontend/src/App.tsx`.
- Added a Hide/Show sidebar toggle with `aria-expanded` and accessible labels.
- Added role and permission summary derived from the selected workspace and current user.
- Added nav button titles/ARIA labels so collapsed navigation remains usable.
- Added collapsed shell CSS: 304px expanded sidebar, 88px collapsed sidebar, compact navigation tokens, hidden nonessential sidebar copy, and adjusted mobile behavior.
- Reworked global CSS tokens and common surfaces to monochrome black/white/gray styling.
- Converted active navigation, buttons, badges, panels, status blocks, and progress states away from teal/soft color accents.

## Validation
Run from repository root:

```bash
cd frontend
npm run test
npm run build
```

Then rebuild the local app:

```bash
docker compose up -d --build frontend
curl -sS -I http://127.0.0.1:5173
```

## Human Review Checklist
- Confirm the Hide/Show control is easy to find.
- Confirm collapsed navigation remains usable from tokens and hover titles.
- Confirm the active page is obvious in both states.
- Confirm the shell reads as a black-and-white admin/developer console.
- Confirm role and permission wording is truthful for current backend support.
- Confirm mobile layout does not hide page content.

## Known Limitations
- Role detection is currently based on workspace ownership because the backend does not yet expose a rich permission matrix.
- Sidebar feature visibility is not deeply role-filtered yet; most pages are still member-readable in the backend.
- Browser screenshot QA remains environment-dependent; Playwright Chromium in this WSL image is missing native libraries.
