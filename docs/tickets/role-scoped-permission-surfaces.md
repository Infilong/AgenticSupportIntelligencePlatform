# Role Scoped Permission Surfaces

## Goal
Make role-specific product surfaces honest across backend APIs and frontend loading. Reviewers and viewers should not receive the same admin/developer surface as owners.

## Context
The UI filtered navigation by permissions, but backend read permissions were broad and frontend workspace refresh eagerly loaded every workspace API. That made restricted roles noisy or overly powerful: a reviewer could be hidden from a page later, but the backend still allowed many admin reads.

## Requirements
- Narrow role permission presets for viewer, reviewer, developer, legacy member, and owner.
- Enforce read permissions on backend APIs, not only write actions.
- Load frontend workspace data only when the current membership includes the matching permission.
- Load only folder types the current role can read or manage, so growing resource lists stay folder-bounded without leaking hidden areas.
- Clear restricted page state instead of showing stale data or global 403 errors.
- Keep owner and developer workflows functional.

## Implementation
- Split backend role presets into base, viewer, reviewer, developer, legacy member, and owner scopes.
- Added permission dependencies to read APIs for data, knowledge, agents, traces, reviews, tools, guardrails, evaluations, costs, budget policy, members, prompts, models, system health, audit logs, attention, and retrieval.
- Changed frontend workspace refresh to load membership first, then conditionally load or clear each product area by permission.
- Added safe audit/system refresh helpers so non-admin actions do not fail after a successful mutation just because audit/system pages are restricted.
- Added resource-folder read checks by folder type: knowledge, dataset, evaluation, and agent folders now require the matching read permission or folder-management permission.
- Added backend tests proving restricted roles cannot read admin/developer APIs or hidden folder types directly.

## Verification
- `cd backend && uv run ruff check app tests/test_auth_workspace.py tests/test_tools.py tests/test_guardrails.py tests/test_prompt_templates.py tests/test_model_configs.py tests/test_budget_policies.py` passed.
- `cd backend && uv run pytest -s tests/test_agents.py tests/test_tools.py tests/test_guardrails.py tests/test_prompt_templates.py tests/test_model_configs.py tests/test_budget_policies.py tests/test_evaluations.py tests/test_resource_folders.py tests/test_knowledge_documents.py tests/test_human_reviews.py tests/test_auth_workspace.py` passed: 106 passed, 1 warning.
- `cd frontend && npm run build` passed.
- `make frontend-e2e-docker` passed: 1 Chromium smoke test passed.

## Risks
- Some existing users with legacy `member` role keep broad build/review access for compatibility, but not full owner admin access.
- Growing frontend resource lists must stay folder-scoped, searchable, and visibly bounded; do not add flat file/resource lists without a folder or compact grouping strategy.
- New role scopes are product decisions. If the desired reviewer/viewer surface changes, update both permission presets and frontend nav/load gates together.

## Interview Notes
Explain this as aligning product UX with backend authorization. A professional AI platform should not merely disable buttons: every read and write surface should be permission-scoped, and the frontend should avoid calling APIs the user cannot access.
