# Sidebar Current Workspace Simplification

## Goal
Reduce the left navigation panel to identity context and the active workspace, while keeping detailed workspace management on the Account page.

## Context
The previous sidebar duplicated workspace management with search, pagination, role details, status details, and readiness indicators. That made the left rail feel like a management page instead of navigation.

## Changes
- Replaced the sidebar workspace switcher with a compact current-workspace summary.
- Kept user identity in the sidebar header through an initials badge and user label.
- Removed the sidebar readiness card from `AppShell`.
- Left detailed workspace selection, pagination, creation, deletion, and permission review in the Account page.

## Verification
- `npm run build` passed in `frontend/`.

## Human Review Checklist
- The left panel should no longer show a workspace list, search box, pagination, or readiness details.
- The current user and active workspace should be visible at a glance.
- Workspace management should remain available through the Account page.
