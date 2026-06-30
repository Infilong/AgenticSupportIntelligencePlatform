# Sidebar Bounded Workspace Finder

## Goal
Allow users to find and switch workspaces from the left panel without letting the sidebar grow into a large management page.

## Context
The sidebar was simplified to only show identity and current workspace. The follow-up design keeps the left panel compact but adds a limited-height workspace finder so users can switch workspace quickly.

## Changes
- Added a search input and bounded scroll window to the sidebar workspace card.
- Workspace list items show only name and simple state: current, open, or archived.
- Detailed workspace management remains on the Account page through the Manage action.
- The sidebar still hides the workspace list when collapsed.

## Verification
- Run `npm run build` in `frontend/`.
- Manually verify many workspaces stay inside the scroll window instead of expanding the sidebar.

## Human Review Checklist
- Sidebar should not become tall when there are many workspaces.
- Searching should filter workspaces without page jumping.
- Clicking a workspace should switch the active workspace.
- Create/delete/permission controls should stay on Account, not in the sidebar.
