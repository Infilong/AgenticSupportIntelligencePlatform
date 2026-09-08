# Project context

## Product and scope

Build a small internal data-processing administration app with RAG and AI agents for English,
Japanese and Chinese. The active [data processing goal](exec-plans/active/data-processing-admin.md)
supersedes the earlier five-area product direction below. Target: Records, Knowledge, Settings
and an embedded admin assistant; persisted inputs, attempts, results and intermediate evidence.
The running UI still uses the earlier layout until the active migration is implemented and verified.
The approved Dify-inspired rebuild replaces the earlier dataset/evaluation-dashboard product.
Use [product spec](product-spec.md) for scope, [architecture](../ARCHITECTURE.md) for ownership,
and the [acceptance audit](audits/simple-admin-acceptance.md) for evidence and limits.

Five areas: Work, Knowledge, Agents, Activity and Settings. Work is the landing page.
The ordinary journey is knowledge upload, agent configuration, support request, cited answer,
human intervention and an inspectable record. Browser and CLI use the same backend.

## Invariants

- Backend owns authentication, authorization, transactions, persistence and accounting.
- Every workspace-owned entity is scoped before data enters retrieval, tools or model context.
- Fixed authority increases through Viewer, Operator, Admin and Owner. Prevent self-promotion
  and removal of the last owner. Retired roles cannot be assigned.
- Agent actions require both initiating-user permission and configured agent capability.
  Approval covers exact action inputs; retries must not repeat completed effects.
- Tasks are durable and bounded by steps, time and budget. Stop is authoritative before
  subsequent steps/actions; in-flight calls may finish and incur charges.
- Retrieve/filter/pack permitted ready knowledge before model calls. Documents are untrusted
  data. Target behavior distinguishes clarification, missing knowledge and genuine admin approval;
  never invent facts. The current graph still routes missing evidence to review pending migration.
- Record model/provider, token use, estimated cost, timings, failures and human interventions.
  Do not expose secrets or private model reasoning. Scoped trace redaction is not universal PII detection.
- Tests use deterministic providers. Real-provider quality is separate and currently unverified.

## Interface and development

Use cohesive modules, normally below 300 lines. Give each feature one primary home; Work and
Activity share run detail. Lists are bounded, important resources searchable, advanced details
collapsed. Preserve drafts on recoverable failures and discard state when workspace/session changes.
Use the [frontend guide](../frontend/README.md) for current modules and visual ownership.

Follow [AGENTS.md](../AGENTS.md), [coding rules](../codingRules.md) and [PLANS](PLANS.md).
Use only OpenAI development tools/skills. Continue within approved scope; do not infer new
features from historical portfolio milestones. Backend evaluation/import APIs and old evidence
may remain, but they do not expand the five-area interface. Preserve unrelated changes and
verified recovery copies. Do not commit unless asked.
