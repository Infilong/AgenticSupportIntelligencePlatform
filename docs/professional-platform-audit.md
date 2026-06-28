# Professional Platform Audit and Roadmap

Date: 2026-06-28

## Scope
This audit evaluates the current Agentic Intelligence Platform against the active redesign goal: a serious black-and-white AI agent platform for developers, admins, reviewers, and viewers. It covers product, frontend UX, backend/API support, permissions, data organization, LangChain/LangGraph platform concepts, traceability, evaluations, cost observability, and admin/developer workflows.

## Best-Practice Findings
- OWASP authorization guidance supports least privilege, deny-by-default, validating permissions on every request, logging sensitive actions, and authorization tests. This directly applies to role-gated delete/archive operations and workspace-scoped object access. Source: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- WCAG 2.2 contrast guidance requires at least 4.5:1 contrast for normal text and strong focus visibility. This supports the requested black-and-white, high-contrast visual system and clear keyboard focus states. Sources: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html and https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html
- WAI-ARIA tree view guidance is relevant for folder/collection navigation once datasets and knowledge documents grow beyond flat lists. Source: https://www.w3.org/WAI/ARIA/apg/patterns/treeview/
- OpenTelemetry trace concepts reinforce that traces should explain execution across spans/steps, latency, status, and errors. This maps to LangGraph runs, graph steps, model calls, tool calls, guardrails, and checkpoints. Source: https://opentelemetry.io/docs/concepts/signals/traces/
- Material navigation drawer guidance supports grouped navigation and persistent/current-page affordances. This maps to a collapsible sidebar with stable compact labels. Source: https://m3.material.io/components/navigation-drawer/guidelines

## Current Product Assessment
The app now has real backend-supported auth, workspaces, document ingestion, retrieval, LangGraph/LangChain execution, traces, human review, evaluations, model/prompt settings, cost ledger, and audit logs. That is much stronger than a basic chatbot.

However, the product still reads as an MVP operations console rather than a mature AI platform because several concepts are incomplete or only observable after a run:
- roles exist only as `owner` and `member`, and backend mutation APIs mostly check only membership
- tools and guardrails are runtime-visible but not first-class configurable resources
- data, knowledge, evaluations, prompts, and models grow as flat lists without folders, collections, archive, or search discipline
- the visual system is still teal-accented and card-heavy, not the requested black-and-white admin/developer console
- the sidebar is structured but not collapsible and not permission-aware
- the dashboard summarizes readiness, but it does not yet show role, permissions, failed runs, high-cost runs, guardrail blocks, tool errors, or evaluation regressions as an attention queue

## Severity-Ranked Gap List

### P0
None currently blocks local demo operation. The app runs and has real backend-supported AI platform behavior.

### P1
- Permission model is too coarse. `require_workspace_member` permits member access; destructive actions need owner/admin/developer/editor-level checks.
- Resource lifecycle is inconsistent. Knowledge documents can be edited and deleted, but datasets, evaluation runs, prompt versions, model configs, and agents cannot be archived/deleted from backend APIs.
- Resource organization is too flat. Upload/import surfaces will become unusable with many documents, datasets, evaluation cases, prompt versions, or model configs unless folder/collection grouping is added.
- Sidebar is not collapsible and does not expose role/permission context.
- Black-and-white professional visual system is not implemented yet.
- Tools and guardrails are not first-class configurable product areas.

### P2
- Dashboard needs stronger task/attention workflow: pending reviews, failed runs, high-cost runs, guardrail blocks, model failures, stale evaluations, and import/indexing problems.
- List endpoints lack pagination/filter/search for large resource counts.
- Prompt/model pages need archive/deactivate management and clearer history filtering.
- Evaluation suite/case organization is missing; evaluations are run-level only.
- Agent management lacks owner, description, recent runs, failure rate, cost/latency summary, tool list, and guardrail summary.

### P3
- Full ABAC/ReBAC permissions, custom roles, and member management.
- Tool registry with schema, permissions, retries, timeouts, and usage history.
- Guardrail policy registry with admin configuration and versioning.
- OpenTelemetry-compatible trace/span export.
- Cloud deployment, Terraform, BigQuery analytics, and managed observability.

## What Feels Toy-Like Now
- Flat forms and flat resource lists dominate several pages.
- A user can create/import many things but cannot consistently organize, archive, or clean them up.
- Permission state is not visible in the UI.
- Current pages mostly assume a single powerful user.
- Some platform concepts are explained in copy, but not modeled as full resources yet.

## Confusing Layout Areas
- Data and Knowledge are separate pages, but both are data-management concepts; they need folder/collection conventions.
- Prompt and model settings are under Admin, but destructive/configuration permissions are not shown.
- Human Review has improved, but the dashboard does not make review tasks feel like the user’s primary work queue.
- Tools and Guardrails appear as trace details, not as navigable platform resources.

## Visual Design Gap
The current CSS uses teal accents, cards, and soft color states. The objective asks for a calmer black-and-white admin/developer console. The next design ticket should define neutral tokens, status badges, focus states, tables, sidebars, empty states, and forms using high contrast and minimal accent color.

## Navigation and Sidebar Problems
- Sidebar is not collapsible.
- Navigation groups are better than before, but still omit first-class Tools and Guardrails pages.
- Current nav does not filter actions by role/permission.
- Current workspace role is not visible near the workspace selector.

## Missing Permission-Aware UX
Original audit finding: the backend only had `WorkspaceRole.owner` and `WorkspaceRole.member`, with most routes enforcing membership but not action-level permissions.

Current status: role presets now include `owner`, `developer`, `reviewer`, `viewer`, and legacy `member`. Key write, operate, review, folder, archive, and destructive routes use backend permission dependencies. Remaining work is to continue applying granular permission dependencies to lower-risk settings surfaces and to add custom enterprise RBAC later if needed.

The UI now shows current role, available permissions, and disabled/restricted controls for major actions. Continue checking future tickets for:
- current role visibility
- allowed actions
- disabled/restricted controls
- clear unavailable-action explanations
- destructive action permission gates

## Missing Task and Attention Workflow
Needed dashboard sections:
- My permissions
- Needs review
- Failed agent runs
- Guardrail blocks
- High-cost runs
- Model/provider failures
- Evaluation regressions
- Import/indexing failures
- Recent traces
- Usage/cost summary

## Backend and Data Model Gaps
- Need role-aware dependencies: viewer/reviewer/developer/admin/owner or a smaller v1 mapping from current roles.
- Need folder/collection models or columns for documents and datasets first.
- Need archive/deactivate fields for agents, prompt templates, model configs, evaluations, and datasets.
- Need audit logs for destructive/archive/move actions.
- Need list filtering by folder, archived state, language, status, owner, and search query.
- Need pagination for resource lists.

## Agent Workflow Gaps
- Agents do not yet expose description, owner, active/archive state, tool set, guardrail policy, recent run stats, failure rate, cost, or latency summaries.
- Tool execution exists in traces, but there is no tool registry.
- Guardrail decisions exist in traces/reviews, but there is no guardrail policy management surface.

## Traceability Gaps
Trace viewer already shows graph steps, model calls, tool calls, guardrails, checkpoints, tokens, latency, and cost. Missing maturity items:
- run list/history page
- filtering by failed/reviewed/high-cost
- explicit span/trace ID semantics
- relationship from agent page to recent runs
- dedicated tool and guardrail history views

## Evaluation Gaps
Evaluations run from JSONL and store metrics, but there is no suite/folder concept, no archive/delete, no regression baseline pinning, and no per-agent evaluation history page.

## Cost and Token Observability Gaps
Cost summary exists, but needs breakdowns by agent, run, high-cost outliers, failed model calls, P50/P95/P99 latency, and budget alerts.

## Recommended Information Architecture
```text
Agentic Intelligence Platform
├── Overview
│   ├── Dashboard
│   └── My Tasks
├── Build
│   ├── Agents
│   ├── Data
│   ├── Knowledge
│   ├── Tools
│   └── Guardrails
├── Operate
│   ├── Runs
│   ├── Traces
│   └── Human Review
├── Evaluate
│   ├── Evaluation Suites
│   ├── Evaluation Runs
│   └── Usage & Costs
├── Admin
│   ├── Workspace
│   ├── Members & Roles
│   ├── Prompts
│   ├── Models & Providers
│   └── Audit Logs
└── Settings
```

## Recommended Sidebar Plan
- Collapsible sidebar with full labels when expanded and compact tokens/icons when collapsed.
- Current page remains obvious in both states.
- Sidebar shows workspace name, role, and permission tier.
- Feature visibility follows backend-proven role permissions.
- Add Tools and Guardrails as first-class nav entries once backend models exist; until then mark runtime coverage honestly.

## Recommended Dashboard Plan
Dashboard sections should answer what happened, why it matters, and what to do next:
- Current workspace and role
- My permissions
- Recommended next action
- Needs review
- Failed/high-risk runs
- Guardrail blocks
- Evaluation quality/regression status
- High-cost or failed model calls
- Data/knowledge indexing status
- Recent traces
- Audit highlights

## Role and Permission-Aware UX Plan
V1 role mapping can stay simple:
- owner/admin: all actions, including destructive cleanup and member management
- developer: configure agents, data, knowledge, prompts, models, run evaluations
- reviewer: human review tasks, traces/citations needed for decisions
- viewer: read-only dashboards, traces, evaluations, costs if permitted

Backend must enforce each action. Frontend should hide or disable controls based on a `/me` or workspace membership/permissions response, but must never be the source of truth.

## Data and Tool Organization Plan
Flat lists must be replaced with folder/collection organization for surfaces that can grow:
```text
Workspace
├── Data folders
│   ├── Datasets
│   └── Imported conversation examples
├── Knowledge folders
│   ├── Policies
│   ├── FAQs
│   ├── Release notes
│   └── Uploaded document versions
├── Agent groups
├── Evaluation suites
├── Prompt families
└── Model provider / purpose groups
```

Implementation should begin with Knowledge and Data because they are upload/import-heavy and visible to users fastest.

## Backend/API Changes Required
- `GET /workspaces/{id}/membership` or include role/permissions in workspace responses.
- Role-aware dependencies and permission tests.
- Folder/collection API for documents and datasets:
  - `GET /resource-folders?resource_type=knowledge_document|dataset`
  - `POST /resource-folders`
  - `PATCH /resource-folders/{id}`
  - `DELETE /resource-folders/{id}` when empty or with explicit move behavior
  - `PATCH /knowledge-documents/{id}` or reindex request accepts `folder_id`
  - dataset import accepts `folder_id`
- Lifecycle APIs:
  - `DELETE /datasets/{id}` or archive-first endpoint
  - archive/deactivate agents
  - archive/delete evaluation runs
  - archive/deactivate prompt templates/model configs
- List filters: folder, archived, language, status, search.
- Audit logs for create/update/delete/archive/move.

## Database/Model Changes Required
- `ResourceFolder`: workspace_id, resource_type, name, parent_folder_id, created_by_user_id, created_at, updated_at.
- Add `folder_id` nullable FK to `knowledge_documents` and `datasets` first.
- Add `archived_at` and possibly `archived_by_user_id` to datasets, agents, evaluation_runs, prompt_templates, and model_configs where hard delete would damage history.
- Add indexes on `(workspace_id, folder_id)`, `(workspace_id, archived_at)`, and search-friendly title/name fields.

## Phased Implementation Roadmap
### Phase 1 Quick Wins
1. Collapsible sidebar and black-and-white visual system.
2. Role summary and role-aware disabled controls.
3. Knowledge/Data folders plus delete/archive lifecycle.
4. Dashboard attention queue for reviews, failures, cost, and indexing.
5. Run/trace list improvements.

### Phase 2 Structural Improvements
1. Member management and role assignment.
2. Tool registry.
3. Guardrail policy registry.
4. Evaluation suites and regression baselines.
5. Pagination/filtering/search across resource lists.

### Phase 3 Advanced Platform Features
1. ABAC/ReBAC permissions.
2. OpenTelemetry trace export.
3. Provider secret management.
4. Budget and rate limit policies.
5. Cloud deployment and analytics warehouse path.

## First Five Implementation Tickets
1. Collapsible sidebar and black-and-white shell.
2. Role summary and permission-aware action model.
3. Resource lifecycle and folders for Knowledge/Data.
4. Workspace dashboard attention queue.
5. Agents page management upgrade with recent runs, failure/cost/latency summaries.

## Risks and Tradeoffs
- UI-only polish would make the app look more professional while preserving weak permission semantics; this is unacceptable for portfolio credibility.
- Hard delete is convenient but risky for traces, audit, prompt/model history, and evaluations. Prefer archive for resources referenced by runs.
- Folder hierarchy improves scaling but can overcomplicate v1. Start with one shared `ResourceFolder` model and apply it first to datasets and knowledge documents.
- Role model can grow complex quickly. Start with explicit backend permission dependencies and a compact role matrix.
