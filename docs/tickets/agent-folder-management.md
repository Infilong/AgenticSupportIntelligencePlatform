# Agent Folder Management

## Goal
Make agent configurations manageable as a growing workspace resource, not a flat dropdown. Agents should be folder-scoped, searchable, movable, and protected by the same resource-folder permission model used by datasets, knowledge documents, and evaluation runs.

## Context
The product goal is a professional AI agent platform. As teams add agents for products, languages, clients, environments, or experiments, a flat agent selector becomes confusing. Existing `ResourceFolder` infrastructure already supports workspace-scoped folders, folder rename/delete, non-empty folder protection, and frontend folder rails.

## Requirements
- Add `folder_id` to `AgentConfig` and API responses.
- Allow creating an agent directly inside an `agent_config` folder.
- Allow listing agents by folder through an optional query parameter.
- Add an agent folder move endpoint protected by `resource_folders:manage`.
- Reject cross-workspace or wrong-resource-type folders.
- Prevent deleting non-empty agent folders.
- Add frontend folder rail, folder-scoped agent library, search, move controls, and bounded list rendering.

## Non-goals
- Do not hard-delete agents; archive remains the lifecycle action so runs and traces stay auditable.
- Do not add nested folder tree UI beyond the existing folder component.
- Do not add backend pagination in this ticket.

## Test Plan
- Backend resource-folder tests for create/list/move/non-empty protection/viewer denial/cross-workspace rejection.
- Backend agent tests for existing run behavior.
- Frontend production build.
- Diff whitespace check.

## Risks
- If the active selected agent is outside the selected folder, the UI can feel inconsistent. The folder selection should select the first visible agent in the chosen folder or clear the selection.
- Future prompt/model/tool catalogs may need similar organization if they become large user-managed libraries.

## Human Review Checklist
- Confirm the Agents page makes folders, current scope, selected agent, and move/archive controls obvious.
- Confirm viewers can read folders but cannot move agents or manage folders.
- Confirm archived agents remain out of the normal active list but historical runs/traces remain accessible.

## Interview Notes
This is an information architecture and governance improvement: a professional platform treats agents as managed workspace assets with ownership, organization, permissions, and auditability, not as a flat demo dropdown.
