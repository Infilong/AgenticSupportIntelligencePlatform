# Product specification

## Purpose

A small, modern internal tool where a team provides knowledge, runs AI support tasks,
supervises agents and inspects accountable results. English, Japanese and Chinese are
first-class. This approved rebuild supersedes the earlier portfolio feature list. Requirements
are distinct from [verification evidence](audits/simple-admin-acceptance.md).

## Five areas

| Area | Primary responsibility |
| --- | --- |
| Work | Landing page; ask questions, follow tasks, handle pending reviews |
| Knowledge | Upload/paste text or Markdown, search, inspect versions, retry, edit and remove |
| Agents | Configure instructions, model, permitted knowledge, actions and budget |
| Activity | Search history and inspect the same run-detail view used by Work |
| Settings | Workspace, members, fixed roles and model-provider configuration |

A user uploads knowledge, sees Ready or an actionable failure, configures an agent, asks a
question and receives a grounded answer with source excerpts and document-version links.
Unsafe requests or insufficient evidence need review. Users can edit an answer, approve or
reject an exact proposed action, stop a run, or start a linked attempt with corrections.
Navigation and reload preserve authoritative state. Ordinary users do not need JSONL,
graph terminology or developer documentation.

## Permissions

| Role | Capabilities |
| --- | --- |
| Viewer | Read permitted work, knowledge and activity |
| Operator | Viewer plus start/stop tasks and resolve reviews |
| Admin | Operator plus knowledge/agent administration and lower-role members |
| Owner | Full workspace administration, privileged roles and provider settings |

Backend checks apply to web, CLI and tool calls. Every resource is workspace-scoped.
Prevent self-promotion and last-owner removal. Agent capability is limited by both configured
allowance and the initiating user's current authority. Provider credentials stay on the backend.

## Agent execution

The bounded agent interprets support requests, retrieves permitted ready evidence, reads a
bounded operational task-history summary, drafts an answer and proposes a category or internal
note. Only exact approved updates execute. No arbitrary shell tools or autonomous agent teams.

States are Queued, Running, Awaiting review, Completed, Failed, Rejected, Stopping and Stopped.
A stop request prevents later steps/actions and records a confirmed terminal outcome. It does
not reverse completed actions or promise cancellation of provider billing. Ownership loss fails
interrupted work without silently replaying it. Linked retries preserve history and recheck
current settings, permissions and budgets; completed effects cannot be duplicated.

Each model call has a ledger entry. Runs record initiator, configuration snapshot, status,
timestamps, duration, ordered steps, sources, model/provider, model latency, tokens, estimated
cost, tool outcomes, errors, retry lineage, interventions and final outcome. Summaries precede
technical detail. Redact sensitive trace fields; store observable results, not private reasoning.
Clearly label mock execution, estimated costs and unavailable measurements.

## Shared API and CLI

One FastAPI backend and PostgreSQL/pgvector database serve both clients. A worker executes
durable tasks. The [CLI](cli.md) provides auth login, workspace list, knowledge add, agent list,
task create, run watch/inspect/stop, and review approve/reject. Require explicit workspace
scope, discoverable help, stable JSON, useful exit codes and secure noninteractive login.
CLI review follows the same exact-action rules. Full settings-screen CLI parity is outside scope.

## Usability and verification

Use consistent typography, spacing, status labels, accessible controls/focus/contrast and
responsive layouts. Keep lists bounded/searchable, empty states useful, errors actionable
and mutation feedback clear. Avoid duplicated dashboards and deeply nested navigation.

Verify the complete EN/JA/ZH journey, ingestion recovery, exact-action approval/rejection,
stop without later effects, reliable records, role denial/isolation and reload in Chrome.
Verify corresponding CLI operations, focused deterministic backend/concurrency tests and a
small multilingual regression set. Verify configured real providers separately or disclose
unavailable verification. Local mock evidence is not a claim of real semantic quality.

## Explicit limits

Keep the existing stack and cohesive modules; maintain setup, architecture, testing, CLI and
agent instructions. Preserve recovery copies and unrelated changes. No workflow canvas,
marketplace, broad integrations, custom role designer or speculative enterprise infrastructure.
Backend evaluation/import functionality may remain as supporting tools; it is not an ordinary
user prerequisite. Deployment evidence does not establish hosted CI, load capacity, enterprise
SSO, offsite recovery or general production certification. See [limitations](known-limitations.md).
